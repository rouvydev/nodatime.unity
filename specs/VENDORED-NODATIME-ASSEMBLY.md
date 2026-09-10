# Vendored NodaTime assembly

**Scope:** upstream — `NodaTime` is written and released by Jon Skeet under Apache-2.0. The
authoritative source for the binary is the `NodaTime` package on nuget.org and
<https://nodatime.org>; this repository only redistributes the compiled output.
**Last verified:** 2026-09-10, by hashing the committed DLL against the official
`NodaTime 2.4.18` NuGet package, against the tzdb blob published on nodatime.org, and
against the `1.0.0` tarball on the GitHub npm registry.

## Intent

This repository is a binary drop: four tracked files, one of which is `NodaTime.dll`. There
is no project file, no `.csproj`, no manifest that records which upstream build the binary
is, and no `.meta` file in git. Everything that makes the package reproducible — which
upstream asset it is, which target framework, which time zone database it carries, and how
the Unity `.meta` GUIDs come into existence — is knowable only by inspecting the binary and
the release workflow. This spec writes it down so a future re-pack does not have to
rediscover it.

## Specification

### What is committed

| | |
|---|---|
| Path | `rouvy.nodatime.unity/Runtime/NodaTime.2.4.18/NodaTime.dll` |
| Size | 465,920 bytes |
| SHA-256 | `dafe5ad09142661547b5d1b1b17798799511ad5c2aa187bddbd6da13fdb95a42` |
| Assembly version | `2.4.18.0` (informational version `2.4.18`) |
| Target framework | `.NETStandard,Version=v2.0` |
| Licence | Apache-2.0 (upstream `.nuspec`) |

### Rules

1. **The binary is the unmodified upstream asset.** Its SHA-256 equals
   `lib/netstandard2.0/NodaTime.dll` inside the official `NodaTime 2.4.18` package on
   nuget.org, byte for byte. It also carries upstream's own build path in its debug
   directory (`…\obj\Release\netstandard2.0\NodaTime.pdb`, from Jon Skeet's tzdb-update
   build tree), so it was never rebuilt or re-signed at Rouvy. **Never hand-edit, re-sign,
   IL-merge or strip it** — a re-pack replaces it wholesale.

2. **`netstandard2.0` is the asset to take.** The package also ships `lib/net45` and
   `lib/netstandard1.3`; both have different hashes and neither is what is vendored here.
   `netstandard1.3` additionally drags in NuGet dependencies (`NETStandard.Library`,
   `System.Runtime.Serialization.Xml`), which is a second reason not to use it.

3. **Nothing else has to be vendored alongside it.** The upstream `.nuspec` declares an
   **empty** dependency group for `.NETStandard2.0`, so `NodaTime.dll` is self-contained on
   this target framework. Re-check that group on any version bump; if a future release adds
   dependencies there, they must be vendored too or Unity will fail to resolve them at
   runtime.

4. **The time zone database is embedded, not downloaded.** The assembly contains the managed
   resource `NodaTime.TimeZones.Tzdb.nzd`, and its bytes are byte-identical to the 136,055-byte
   `tzdb2022a.nzd` published at <https://nodatime.org/tzdb/tzdb2022a.nzd>. So the vendored
   package pins **tzdb 2022a**, offline, with no network access and no side-car data file.
   Consumers get whatever tzdb version the DLL was built with — the only way to move it
   forward is to vendor a newer `NodaTime.dll`.
   Inside that same blob the CLDR Windows-time-zone mapping is stamped with tzdb version
   `2021a` and Windows version `7e11800`; the mapping table lags the zone data upstream and
   that is upstream's business, not a packaging defect.

5. **The directory name carries the version, and the version is the only place it is
   recorded.** `Runtime/NodaTime.<version>/NodaTime.dll` — the convention `package.json`
   states as *"Every dll has its version defined in the directory name."* A re-pack creates
   a new directory and removes the old one; it never overwrites the DLL in place under a
   name that no longer matches.

6. **`.meta` files are generated at publish time and are not in git.** `.github/workflows/release.yml`
   runs `rouvydev/metagen-gha@v1.4` over `./rouvy.nodatime.unity` with a fixed seed before
   `npm publish`. Do not commit `.meta` files, and **do not change the `seed` input**: the
   GUID for each asset is `XXHash128` keyed by that seed and fed the asset's path
   (see `src/index.js` of `rouvydev/metagen-gha`), so the seed and the path together decide
   the GUID.

7. **Renaming the version directory changes GUIDs — by design.** Because the GUID is a
   function of the path, a re-pack that moves the DLL from `NodaTime.2.4.18/` to
   `NodaTime.<new>/` yields a new folder GUID and a new DLL GUID. That is acceptable here
   only because consumers reference the assembly by name, not by GUID: nothing in `rouvyapp`
   or `rouvyugc` stores a GUID for this DLL (neither repository tracks a `.meta` for it).
   The GUIDs the published `1.0.0` carries are, for the record:

   | Asset | GUID |
   |---|---|
   | `Runtime` | `91d3d8babc60bcbdbd07e21fb09b9020` |
   | `Runtime/NodaTime.2.4.18` | `4cbeca9ab20e415b6966790834ac1f89` |
   | `Runtime/NodaTime.2.4.18/NodaTime.dll` | `f54f6b0f9c945f0b243441bf7c2076ed` |
   | `package.json` | `4692cb5e7a6ca2c4e61d1502bfe4c398` |

8. **The generated plugin importer settings are metagen's fixed template, not a choice made
   for this package.** The `NodaTime.dll.meta` in the published tarball sets `Any: enabled 1`,
   `Editor: enabled 0` and `Windows Store Apps: enabled 0`. metagen-gha emits exactly that
   block for every `.dll` it processes, so it says nothing about this assembly's
   requirements, and there is no per-package way to override it short of committing a
   `.meta` (which rule 6 forbids) or changing the action.

9. **Consumers pin an exact version.** `rouvydev/rouvyapp` and `rouvydev/rouvyugc` both carry
   `"rouvy.nodatime.unity": "1.0.0"` in `Packages/manifest.json`, so a publish reaches them
   only when their own manifest is bumped. Both use the library from
   `Assets/Scripts/Backend/Utils/DateTimeUtils.cs`; `rouvyugc` also from
   `Assets/Scripts/UI/Screens/Cutting/CuttingScreen.cs`.

10. **The package version and the upstream version are independent.** `package.json` says
    `1.0.0`; the vendored library says `2.4.18`. Only `package.json`'s `version` is what the
    registry and consumers see, and it must be bumped for a re-pack to be publishable at all
    — the registry rejects a re-publish of an existing version.

## Definition of done

Verifiable outcomes for a re-pack:

- [ ] The new DLL's SHA-256 equals `lib/netstandard2.0/NodaTime.dll` in the upstream NuGet
      package for the version being vendored, and this spec's table records the new hash,
      size, version and TFM.
- [ ] The upstream `.NETStandard2.0` dependency group was re-checked (rule 3) and either is
      empty or every dependency was vendored.
- [ ] The tzdb version in rule 4 was re-established from the new binary, not carried over.
- [ ] `Runtime/NodaTime.<old>/` is gone and `Runtime/NodaTime.<new>/` is in its place.
- [ ] `version` in `rouvy.nodatime.unity/package.json` is bumped and its `description`
      names the new upstream version.
- [ ] No `.meta` file was committed and `release.yml`'s `seed` is unchanged.
- [ ] `rouvyapp` and `rouvyugc` manifests are bumped in their own pull requests, or the
      publish is knowingly left unconsumed.

## Non-goals

- **The NodaTime API.** <https://nodatime.org/2.4.x/userguide/> is authoritative; this spec
  covers only which binary is vendored and how it is packaged.
- **Whether to move to NodaTime 3.x.** 2.4.18 is one major version behind upstream (latest
  on nuget.org is 3.3.3). That is a product decision with a consumer-side migration
  attached, tracked separately from this packaging spec.
- **Managed code stripping.** The package ships no `link.xml` and no
  `IUnityLinkerProcessor` callback, and no `link.xml` exists anywhere in the `rouvydev`
  organisation, so there is nothing to specify. Note that a `link.xml` inside a
  registry-resolved package would not be picked up by `UnityLinker` anyway — the sibling
  `rouvy-unity-zeroconf-package` documents that dead end and the editor-callback workaround.
  Embedded resources such as the tzdb blob are not removed by managed stripping; only unused
  code is.

## Technical notes

- **The Release workflow in this repository has never run.** The GitHub Actions API reports
  `total_count: 0` for `rouvydev/nodatime.unity`, yet `rouvy.nodatime.unity@1.0.0` was
  published on 2023-10-20 and its tarball does carry metagen-shaped `.meta` files. So the
  published artifact matches what `release.yml` would produce, but the workflow itself is
  **unproven in CI** — whoever runs it first for a re-pack should expect to debug it
  (`actions/checkout@v3` and `actions/setup-node@v3` with Node 16 are all well past their
  support window). This is stated as a caveat, not a defect: the publish route was not
  verified end to end while writing this spec.
- Every hash and byte count above was produced by reading the files, not copied from a
  release note. The commands are in the `repack-nodatime-version` skill so they can be
  re-run rather than trusted.
- The repository redistributes an Apache-2.0 binary publicly and ships **no `LICENSE`,
  `NOTICE` or attribution file**. Whether that needs fixing is a call for a human; this spec
  only records the state.

## References

- Upstream package: <https://www.nuget.org/packages/NodaTime/2.4.18>
- Upstream tzdb downloads: <https://nodatime.org/tzdb/>
- `.claude/skills/repack-nodatime-version/SKILL.md` — the procedure that applies this spec.
- [`../.github/workflows/release.yml`](../.github/workflows/release.yml) — the publish path.
- `rouvydev/metagen-gha` — the `.meta` generator and its GUID derivation.
