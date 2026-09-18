---
name: repack-nodatime-version
description: Re-packs the vendored NodaTime.dll in rouvy.nodatime.unity onto a different upstream NodaTime version, or verifies that the DLL already committed is the untouched upstream asset. Covers picking the netstandard2.0 asset from nuget.org, reading the embedded tzdb version out of the binary, the versioned Runtime/NodaTime.<version>/ directory convention, the package.json bump and the consumers that pin it. Use when asked to upgrade, bump, re-pack or verify NodaTime in this repository, when checking which upstream build or which time zone database the committed DLL is, or before publishing rouvy.nodatime.unity.
---

# Re-pack the vendored NodaTime version

This repository redistributes one upstream binary. Read
`specs/VENDORED-NODATIME-ASSEMBLY.md` first — it holds the rules, the current hash, and the
reasons behind each step here. This skill is only the procedure.

**A re-pack replaces the DLL wholesale.** Never hand-edit, re-sign or IL-merge it, and never
commit a `.meta` file.

## Verifying what is already committed

Do this before claiming anything about the vendored build. Every value in the spec came from
these commands, so they are also how you check the spec has not drifted.

```bash
DLL=rouvy.nodatime.unity/Runtime/NodaTime.2.4.18/NodaTime.dll
shasum -a 256 "$DLL"                                    # expect the hash in the spec
strings -a "$DLL" | grep -E 'NETStandard,Version|^2\.4\.18'   # target framework + version
strings -a "$DLL" | grep -F 'NodaTime.TimeZones.Tzdb.nzd'     # tzdb is embedded, not a side-car
```

Confirm it is upstream's own asset rather than a local build, by hashing the same file out of
the official NuGet package:

```bash
curl -sSL -o /tmp/nodatime.nupkg https://www.nuget.org/api/v2/package/NodaTime/2.4.18
unzip -p /tmp/nodatime.nupkg lib/netstandard2.0/NodaTime.dll | shasum -a 256
```

The two hashes must match. To pin the **tzdb** version, download the candidate blob from
<https://nodatime.org/tzdb/> and test for it inside the assembly — the embedded resource is
the published file verbatim:

```bash
curl -sSL -o /tmp/tzdb2022a.nzd https://nodatime.org/tzdb/tzdb2022a.nzd
python3 -c "import sys;d=open(sys.argv[1],'rb').read();n=open(sys.argv[2],'rb').read();print(d.find(n)>=0)" \
  "$DLL" /tmp/tzdb2022a.nzd
```

## Re-packing onto a new upstream version

1. **Take the `netstandard2.0` asset, nothing else.** Download
   `https://www.nuget.org/api/v2/package/NodaTime/<version>`, extract
   `lib/netstandard2.0/NodaTime.dll`, and record its SHA-256.
2. **Re-check the dependency group.** Read `NodaTime.nuspec` from the same package and
   confirm the `.NETStandard2.0` group is still empty. If it is not, every dependency has to
   be vendored the same way or Unity will not resolve it in the player — that turns a
   one-file bump into a multi-assembly re-pack, so raise it rather than improvising.
3. **Create the new versioned directory and delete the old one.**
   `rouvy.nodatime.unity/Runtime/NodaTime.<version>/NodaTime.dll`. The directory name is the
   only record of the upstream version in the tree, so it must match exactly.
4. **Bump `rouvy.nodatime.unity/package.json`**: `version` (semver, and the registry rejects
   a re-publish of an existing version) and the `description`, which names the NodaTime
   version. A major NodaTime bump is a major bump here — the assembly is visible to consumer
   code.
5. **Establish the new tzdb version from the new binary** with the check above, and update
   the spec's table, hash, size and tzdb rule in the same change. Do not carry the old value
   forward.
6. **Leave `.github/workflows/release.yml` alone**, especially the `seed` input. Publishing
   is a manual `workflow_dispatch` run of that workflow; it generates the `.meta` files and
   runs `npm publish`. Note that the workflow has **never executed in this repository** — see
   the spec's technical notes — so budget time for it failing on its Node 16 and
   `actions/*@v3` steps, and do not "fix" it silently as part of a version bump.
7. **Bump the consumers separately.** `rouvydev/rouvyapp` and `rouvydev/rouvyugc` pin an
   exact version in `Packages/manifest.json`; a publish reaches neither until their own
   manifests change, in their own pull requests.

## Going to NodaTime 3.x

Treat it as a product decision, not a re-pack. 2.4.18 is one major version behind upstream,
and 3.x has source-breaking API changes that both consumers compile against. Confirm the
scope before starting, and check `netstandard2.0` is still an offered target framework for
the version chosen.

## What this repository has no answer for

- **Managed code stripping.** No `link.xml` and no linker callback in this package. If
  IL2CPP ever strips something NodaTime needs reflectively, the fix cannot be a `link.xml`
  committed inside this package — `UnityLinker` does not read descriptors from
  registry-resolved packages. See the spec's non-goals.
- **The plugin importer settings.** They come from a fixed template inside
  `rouvydev/metagen-gha`, identical for every DLL it processes, and cannot be tuned per
  package without committing a `.meta` (which the spec forbids) or changing the action.
