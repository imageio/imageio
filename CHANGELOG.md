# Changelog / release notes

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## v2.21.1 (2022-08-08)
### Fix
* Seeking to last frame caused EoF in pyav ([#855](https://github.com/imageio/imageio/issues/855)) ([`7ff7f02`](https://github.com/imageio/imageio/commit/7ff7f023d4b24a8349c867a50c46cfe52ce724bb))

## v2.21.0 (2022-08-01)
### Fix
* Write single TIFF page for single RGB image ([#851](https://github.com/imageio/imageio/issues/851)) ([`0f04bc9`](https://github.com/imageio/imageio/commit/0f04bc9cb7f03c964cc978f6c1049879e5a90100))

### Feature
* Add is_batch kwarg to pillow ([#845](https://github.com/imageio/imageio/issues/845)) ([`21d5c73`](https://github.com/imageio/imageio/commit/21d5c73f3f19ba2093495dfd13a276acb56412e6))

### Other
* Add a migration note about pillow squeezing ([#850](https://github.com/imageio/imageio/issues/850)) ([`7c55a55`](https://github.com/imageio/imageio/commit/7c55a557c0feb1426bf8fff5a8f61b6f05d305d9))
* Add missin option to imwrite type hints ([#848](https://github.com/imageio/imageio/issues/848)) ([`6da4a42`](https://github.com/imageio/imageio/commit/6da4a426a1bd3e11e679f0fb4fec5201a4fffa88))
* Ignore exclude_applied on legacy plugins ([#844](https://github.com/imageio/imageio/issues/844)) ([`f082dde`](https://github.com/imageio/imageio/commit/f082dde8259865804698d8558f36e9fdeb1bfcb9))
* Remove unneeded CD steps ([#847](https://github.com/imageio/imageio/issues/847)) ([`0d99c51`](https://github.com/imageio/imageio/commit/0d99c51e44d13b49668ef07ae9a8af93084e38a8))

## v2.20.0 (2022-07-25)
### Fix
* Expose frame-level metadata and duration in pyav ([#839](https://github.com/imageio/imageio/issues/839)) ([`05fcf2c`](https://github.com/imageio/imageio/commit/05fcf2c443edf78e1807670ba304f51a43c74808))

### Feature
* Enable HTTP based streams in pyav ([#838](https://github.com/imageio/imageio/issues/838)) ([`fb1150d`](https://github.com/imageio/imageio/commit/fb1150d3fd5a00db036ffb4c603cedeed3a1634f))

### Other
* Fix typo in test_pyav ([#846](https://github.com/imageio/imageio/issues/846)) ([`f89abf1`](https://github.com/imageio/imageio/commit/f89abf18cd56ba5d8da1939b807c0f3f1e593e0b))

## v2.19.5 (2022-07-18)
### Fix
* Allow multiple reads from imopen ([#830](https://github.com/imageio/imageio/issues/830)) ([`18e3cb6`](https://github.com/imageio/imageio/commit/18e3cb6d3228ac1ca27160d0e6c91e720213dd9f))

### Other
* Fix typos in v3 narrative docs. ([#835](https://github.com/imageio/imageio/issues/835)) ([`d68f16b`](https://github.com/imageio/imageio/commit/d68f16baaf2f6fcfe8523dec4227203e8b22797a))
* Point source links to github ([#834](https://github.com/imageio/imageio/issues/834)) ([`20eef2a`](https://github.com/imageio/imageio/commit/20eef2a3ead7e892b18e7726260b9bf652217527))
* Remove outdated numpy minimum version ([#833](https://github.com/imageio/imageio/issues/833)) ([`39947a7`](https://github.com/imageio/imageio/commit/39947a7506d4d7a28b6402ddcce9211e6ccfbe84))

## v2.19.4 (2022-07-11)
### Fix
* Resolve infinite recursion in python 3.11 (and add CI for pypy-3.9) ([#826](https://github.com/imageio/imageio/issues/826)) ([`301f941`](https://github.com/imageio/imageio/commit/301f941d334e1b3a8c0aa9cebd3d2ea883645fc1))
* Include PYI files in package ([#825](https://github.com/imageio/imageio/issues/825)) ([`fff16fb`](https://github.com/imageio/imageio/commit/fff16fb915b75beb7a6f8f3dd118d8ab02051dc4))

### Other
* Fix typo in readme ([#828](https://github.com/imageio/imageio/issues/828)) ([`67dac41`](https://github.com/imageio/imageio/commit/67dac41184c230fb3158100080dbec68bc61c98d))
* Add quotes to "I" in GIF optimization example ([#823](https://github.com/imageio/imageio/issues/823)) ([`9fd2b35`](https://github.com/imageio/imageio/commit/9fd2b3504ee7dd55bb7f717fafdf5ae6fe0a294f))

## v2.19.3 (2022-05-30)
### Fix
* Correctly read STK volumes in v3 ([#805](https://github.com/imageio/imageio/issues/805)) ([`9b739ab`](https://github.com/imageio/imageio/commit/9b739abebcab6b7364863bc4f25bcdc5b8c8c1a7))

### Other
* Include py.typed in package ([#815](https://github.com/imageio/imageio/issues/815)) ([`ba63485`](https://github.com/imageio/imageio/commit/ba63485e82bc7eec9399037375887d22ad0a6c82))
* Add GA token ([#814](https://github.com/imageio/imageio/issues/814)) ([`c9a2852`](https://github.com/imageio/imageio/commit/c9a2852bbdca166cff546a99f65ef1057e34dd38))

## v2.19.2 (2022-05-16)
### Fix
* Don't treat im_mode ? as im_mode V ([#811](https://github.com/imageio/imageio/issues/811)) ([`45739d5`](https://github.com/imageio/imageio/commit/45739d5507f75095ae8dc34049b55432c5dc288c))

### Other
* Add stacklevel=2 to some warnings. ([#813](https://github.com/imageio/imageio/issues/813)) ([`75edcee`](https://github.com/imageio/imageio/commit/75edcee181631be4ab6f6a69c5d93982c7381bd9))

## v2.19.1 (2022-05-09)
### Fix
* Reset request when iterating over plugins ([#792](https://github.com/imageio/imageio/issues/792)) ([`46a49c4`](https://github.com/imageio/imageio/commit/46a49c442a743d9afe7721ebde59e190f84f60e6))
* Rename format_hint to extension and prefer it over actual file extensions ([#807](https://github.com/imageio/imageio/issues/807)) ([`4830f15`](https://github.com/imageio/imageio/commit/4830f1582cbe8963259652709e44f4d4559d84f2))

### Other
* Fix broken links in readme ([#806](https://github.com/imageio/imageio/issues/806)) ([`52954bc`](https://github.com/imageio/imageio/commit/52954bcedcc3987b9437cde218840543905c05bb))

## v2.19.0 (2022-05-02)
### Feature
* OpenCV plugin ([#791](https://github.com/imageio/imageio/issues/791)) ([`36c56a8`](https://github.com/imageio/imageio/commit/36c56a84e5cbb2383a55b6fe670429e055c7cdc8))

## v2.18.0 (2022-04-25)
### Fix
* Do not pass optional kwargs by position in tifffile ([#794](https://github.com/imageio/imageio/issues/794)) ([`512fe11`](https://github.com/imageio/imageio/commit/512fe117fe4d31dd2617e7875b80826dddf46871))
* Ensure pts increases even if pyav doesn't flush the frame immediately ([#787](https://github.com/imageio/imageio/issues/787)) ([`5b74e8d`](https://github.com/imageio/imageio/commit/5b74e8d26fa530d831d49d04a739c022c90d4258))

### Feature
* Allow writing bayer formats in pyav ([#788](https://github.com/imageio/imageio/issues/788)) ([`4596262`](https://github.com/imageio/imageio/commit/45962620f592f4efeb2df73357191626f2eee129))

### Other
* Update imopen types ([#793](https://github.com/imageio/imageio/issues/793)) ([`7ecea02`](https://github.com/imageio/imageio/commit/7ecea02d7c5633c1aa8afe39af6f4f0de59d8ae3))

## v2.17.0 (2022-04-18)
### Feature
* New Plugin for pyAV ([#745](https://github.com/imageio/imageio/issues/745)) ([`22ab97e`](https://github.com/imageio/imageio/commit/22ab97ea0facccfb1c888fb1a8fafded1a0e0f78))
* Add plugin default sentinel ([#779](https://github.com/imageio/imageio/issues/779)) ([`d1d13ef`](https://github.com/imageio/imageio/commit/d1d13ef4fe1e8ac7538ceb81f0e8e7612413c771))

### Other
* Better Type Annotations + mypy support ([#784](https://github.com/imageio/imageio/issues/784)) ([`607600d`](https://github.com/imageio/imageio/commit/607600d92d9eb454df5320b4b4d6047aeb5a567d))
* Add fast-paths for pyav formats ([#785](https://github.com/imageio/imageio/issues/785)) ([`13cb5e2`](https://github.com/imageio/imageio/commit/13cb5e2899e30c9a30456b83bd7f16a72dbfc5e0))
* Update readme ([#786](https://github.com/imageio/imageio/issues/786)) ([`7f1bb1d`](https://github.com/imageio/imageio/commit/7f1bb1d6fb185ae7aa5c182ef8eea3216a42f622))
* Fix docs on standard images ([#783](https://github.com/imageio/imageio/issues/783)) ([`7c65efa`](https://github.com/imageio/imageio/commit/7c65efae21554309767a9df95ecc3032e33712a1))

## v2.16.2 (2022-04-11)
### Fix
* Handle PIL paletts with <256 color palettes ([#775](https://github.com/imageio/imageio/issues/775)) ([`309242d`](https://github.com/imageio/imageio/commit/309242d42bf43103290ee57934e9b64abd0fac9f))
* Set spacing to None by default ([#773](https://github.com/imageio/imageio/issues/773)) ([`1b93434`](https://github.com/imageio/imageio/commit/1b93434f9b4798e966b68c18f0b39d05f817d247))

### Other
* Deprecation warnings to transition to v3 ([#769](https://github.com/imageio/imageio/issues/769)) ([`fba08a7`](https://github.com/imageio/imageio/commit/fba08a76fdef1921925139e1b55fc91e442b8a71))
* Remove unused test file ([#780](https://github.com/imageio/imageio/issues/780)) ([`9f8d296`](https://github.com/imageio/imageio/commit/9f8d2968a51a94f084f9f8e109b4b0398c1c8e56))
* Update license ([#771](https://github.com/imageio/imageio/issues/771)) ([`ec9de36`](https://github.com/imageio/imageio/commit/ec9de36750b3191bc337e8625372ee23e8876154))
* Build docs using python 3.10 ([#770](https://github.com/imageio/imageio/issues/770)) ([`8b563f5`](https://github.com/imageio/imageio/commit/8b563f5663cad5e7dd767606c63539b5bab79aea))
* Note on preferring venv ([#768](https://github.com/imageio/imageio/issues/768)) ([`cd25e19`](https://github.com/imageio/imageio/commit/cd25e1948701b3bd83ba47abdfab02f034b8906c))
* V3 API docs ([#718](https://github.com/imageio/imageio/issues/718)) ([`6c47524`](https://github.com/imageio/imageio/commit/6c475242282823a73573164fd180dd78871588a4))
* Update DOI ([#764](https://github.com/imageio/imageio/issues/764)) ([`2cf60c1`](https://github.com/imageio/imageio/commit/2cf60c1a524ffd158e3a3f5578dc5ecdcb8c9362))
* Cleanly determine write format in pillow ([#752](https://github.com/imageio/imageio/issues/752)) ([`8cba510`](https://github.com/imageio/imageio/commit/8cba5105ec51650d1c8d8273c63d6b76a7fa9627))

## v2.16.1 (2022-02-28)
### Fix
* Ignore TIFF ``XResolution`` or ``YResolution`` with 0 in the denominator. ([#753](https://github.com/imageio/imageio/issues/753)) ([`6b44a1b`](https://github.com/imageio/imageio/commit/6b44a1beb6db73eb53372debf99bb2e24450546f))

### Other
* Add section on freezing ([#759](https://github.com/imageio/imageio/issues/759)) ([`7699e32`](https://github.com/imageio/imageio/commit/7699e32cee4f48bebdd8ace6a24c05b03ce75eec))
* Update "python_requires" to 3.7+ ([#757](https://github.com/imageio/imageio/issues/757)) ([`f80f068`](https://github.com/imageio/imageio/commit/f80f068329123fc3c164c522391969ac8eeb0dd4))

## v2.16.0 (2022-02-14)
### Fix
* Read metadata of current frame when iterating + APNG fast path ([#750](https://github.com/imageio/imageio/issues/750)) ([`87f290a`](https://github.com/imageio/imageio/commit/87f290a074cbb4e856d6c68e7f0ddb2c9ca904cc))

### Feature
* Improps and immeta ([#739](https://github.com/imageio/imageio/issues/739)) ([`05d6f33`](https://github.com/imageio/imageio/commit/05d6f3332c8d072e253e9fceda3e8bbfbe4c8df1))

### Other
* Dedicated namespaces for APIs ([#720](https://github.com/imageio/imageio/issues/720)) ([`c0c032a`](https://github.com/imageio/imageio/commit/c0c032a7fa97c8771f9bdd61ac628ac0c7630dee))

## v2.15.0 (2022-02-07)
### Fix
* Fix webcam FPS settings on MacOS ([#738](https://github.com/imageio/imageio/issues/738)) ([`a08b0c4`](https://github.com/imageio/imageio/commit/a08b0c45b035b1630a93b3ebe7f1dc628d83f952))

### Feature
* Add format_hint to v3 API ([#734](https://github.com/imageio/imageio/issues/734)) ([`dd538ec`](https://github.com/imageio/imageio/commit/dd538eca734132191635b2b767566d437b3e542b))
* Make tifffile read `resolution` metadata ([#732](https://github.com/imageio/imageio/issues/732)) ([`4f7f334`](https://github.com/imageio/imageio/commit/4f7f334893a07964cba5bb2b96f238095d2813e8))

### Other
* Make RTD fail on warnings during CI ([#747](https://github.com/imageio/imageio/issues/747)) ([`252839c`](https://github.com/imageio/imageio/commit/252839c367e7a04a141237c2d953f09375dc73b9))
* Add missing ! to download tracker banner ([#746](https://github.com/imageio/imageio/issues/746)) ([`8e8c546`](https://github.com/imageio/imageio/commit/8e8c5466a66b80119c36bb4fb4f37f6ebd92b06f))
* Remove link to download tracker ([#744](https://github.com/imageio/imageio/issues/744)) ([`33fe89f`](https://github.com/imageio/imageio/commit/33fe89fa4ea3820efb65ce467c24b06fb7b05cb6))
* Type annotations for pillow ([#743](https://github.com/imageio/imageio/issues/743)) ([`269d9e1`](https://github.com/imageio/imageio/commit/269d9e1839a4a91debec11ec44822cb03e6018e6))
* Contribution guidelines ([#729](https://github.com/imageio/imageio/issues/729)) ([`ff2e3fd`](https://github.com/imageio/imageio/commit/ff2e3fde245b1f237c68072430f67e8bd748d94d))
* Deprecate python 3.6 support ([#740](https://github.com/imageio/imageio/issues/740)) ([`e104505`](https://github.com/imageio/imageio/commit/e104505d4b5a53b11fd0023c83829795d4b31853))

## v2.14.1 (2022-01-24)
### Fix
* Avoid raw bytes in exception message ([#733](https://github.com/imageio/imageio/issues/733)) ([`6252636`](https://github.com/imageio/imageio/commit/625263647cf1d564e43882ce1356fae4967569ed))

## v2.14.0 (2022-01-20)
### Fix
* Handle pillow9 GIFs ([#724](https://github.com/imageio/imageio/issues/724)) ([`836b7a9`](https://github.com/imageio/imageio/commit/836b7a9b077a96de8adab5b67ea53b1292048275))

### Feature
* Allow mode=None when writing with pillow ([#722](https://github.com/imageio/imageio/issues/722)) ([`7be2712`](https://github.com/imageio/imageio/commit/7be271234b4aa2e9fd9aa5387fa0d07044461387))

### Other
* Add repo to PYTHONPATH in `should_release?` ([#728](https://github.com/imageio/imageio/issues/728)) ([`a22d810`](https://github.com/imageio/imageio/commit/a22d810657f54df6ca9f55f76e3225b9b826b1cb))
* Reorganize commit tags ([#717](https://github.com/imageio/imageio/issues/717)) ([`c57bf85`](https://github.com/imageio/imageio/commit/c57bf859608b1dea87c18473857eaca92a00396e))
* Reduce release frequency to weekly ([#716](https://github.com/imageio/imageio/issues/716)) ([`51f552b`](https://github.com/imageio/imageio/commit/51f552ba5ed4aa771f205a2798e1fd3859fb2942))

## v2.13.5 (2021-12-23)
### Fix
* Clean up PillowPlugin destructor ([#714](https://github.com/imageio/imageio/issues/714)) ([`104171b`](https://github.com/imageio/imageio/commit/104171be5f8e0ab9a3bf7d8aa7f1818901b0755e))
* Close standard streams after webcam access ([#711](https://github.com/imageio/imageio/issues/711)) ([`9c434e0`](https://github.com/imageio/imageio/commit/9c434e023ad38b302f165aceac88b602c3a5e28c))

## v2.13.4 (2021-12-21)
### Fix
* Update tested pypy versions ([#713](https://github.com/imageio/imageio/issues/713)) ([`8a79104`](https://github.com/imageio/imageio/commit/8a7910481b025ffaf3004b20b63a13ce0495d732))

### Documentation
* Update download tracker ([#712](https://github.com/imageio/imageio/issues/712)) ([`a265c51`](https://github.com/imageio/imageio/commit/a265c5110f3684bb2893bf2c76d9a839f03a82de))

## v2.13.3 (2021-12-08)
### Fix
* Allow TIFF to write bytes and file objects ([#704](https://github.com/imageio/imageio/issues/704)) ([`9c765c3`](https://github.com/imageio/imageio/commit/9c765c3e7dcf800910b348294261c05034fcedb9))

## v2.13.2 (2021-12-07)
### Fix
* Only force webcam FPS on Mac ([#701](https://github.com/imageio/imageio/issues/701)) ([`28b1d0d`](https://github.com/imageio/imageio/commit/28b1d0db00059dcaebeb9f9a83501d1865e9ceb6))

## v2.13.1 (2021-12-01)
### Fix
* Only run CD on main and fail fast ([#698](https://github.com/imageio/imageio/issues/698)) ([`e90494a`](https://github.com/imageio/imageio/commit/e90494abff407c90ddad422a9f35bf719fc66932))
* Lazy-import plugin namespace ([#693](https://github.com/imageio/imageio/issues/693)) ([`73695ae`](https://github.com/imageio/imageio/commit/73695aef2e0f7ac0dbf705ec544769b036ce08f2))

## v2.13.0 (2021-11-29)
### Documentation
* Fix typos. ([#696](https://github.com/imageio/imageio/issues/696)) ([`67239f3`](https://github.com/imageio/imageio/commit/67239f39c6a13b1bc29bf584eaf2d0dc2e869b9c))

## v2.12.0 (2021-11-24)
### Feature
* Allow plugin objects in plugin kwarg ([#689](https://github.com/imageio/imageio/issues/689)) ([`8f0f689`](https://github.com/imageio/imageio/commit/8f0f689c3a99032c89360bb4dfa6704638a6e0c9))

## v2.11.1 (2021-11-20)
### Fix
* Fix BytesIO regression for legacy pillow ([#688](https://github.com/imageio/imageio/issues/688)) ([`924e1c5`](https://github.com/imageio/imageio/commit/924e1c5c43576acf16247c3c47b7baf6c6f68fe6))

## v2.11.0 (2021-11-18)
### Feature
* Choose plugin based on extension and plugin lazy-import ([#680](https://github.com/imageio/imageio/issues/680)) ([`bdbe699`](https://github.com/imageio/imageio/commit/bdbe699bbcda4223b0b6bd4d7474f84bbe34af09))

## v2.10.5 (2021-11-17)
### Fix
* Resolve regression on imageJ TIFF hyperstacks ([#682](https://github.com/imageio/imageio/issues/682)) ([`7dc9b25`](https://github.com/imageio/imageio/commit/7dc9b25ce50069f17afa464bafe6627b08ffdd6b))

## v2.10.4 (2021-11-13)
### Fix
* Consistently handle file opening/closing ([#673](https://github.com/imageio/imageio/issues/673)) ([`b852f45`](https://github.com/imageio/imageio/commit/b852f451a0d5b2e949f5e698b0ef50a4ec4dbb86))

### Documentation
* Reorder getting started menu ([#683](https://github.com/imageio/imageio/issues/683)) ([`94f479e`](https://github.com/imageio/imageio/commit/94f479ebd4161425d0ce4d4d3aeac1a1802ae3ab))

## v2.10.3 (2021-11-06)
### Fix
* Fix file extension bug when filename contains '#'. ([#678](https://github.com/imageio/imageio/issues/678)) ([`f3fa631`](https://github.com/imageio/imageio/commit/f3fa6318ebd6005ebf2361438795cfbf87e62f7c))

## v2.10.2 (2021-11-05)
### Fix
* Allow devices above <video9> in ffmpeg ([#675](https://github.com/imageio/imageio/issues/675)) ([`1fc4208`](https://github.com/imageio/imageio/commit/1fc420848511cf78765d7862961b89166ba65430))

### Documentation
*  Align README.md with new docs ([#672](https://github.com/imageio/imageio/issues/672)) ([`51a8cd5`](https://github.com/imageio/imageio/commit/51a8cd57cd2ea2722523206e61b617556c725f25))

## v2.10.1 (2021-10-27)
### Fix
* Install ImageIO dependencies during release wheel build ([#671](https://github.com/imageio/imageio/issues/671)) ([`f1ee22a`](https://github.com/imageio/imageio/commit/f1ee22ac1375e67cc8da6822326e10f6badf332c))

## v2.10.0 (2021-10-27)
### Feature
* Allow pillow to write/encode to byte strings ([#669](https://github.com/imageio/imageio/issues/669)) ([`b5df806`](https://github.com/imageio/imageio/commit/b5df8065d980ce1a664cea3c22dc90f066653497))
* Add CD pipeline ([#667](https://github.com/imageio/imageio/issues/667)) ([`6dce3ab`](https://github.com/imageio/imageio/commit/6dce3ab5581a3049658304ef04d3c748ae2b4384))
* Fail PIL write if extension isnt supported ([`0dc33d3`](https://github.com/imageio/imageio/commit/0dc33d3e13f4c2c3f9b9f7e1622a26d0e8338ef7))
* Make imopen use core.Request ([`c51fdb0`](https://github.com/imageio/imageio/commit/c51fdb06b21596a35e9d36f3090ccef9b710fa07))

### Fix
* Bump pillow to 8.3.2 ([#661](https://github.com/imageio/imageio/issues/661)) ([`a5ce49f`](https://github.com/imageio/imageio/commit/a5ce49f1604b15f9566e89e476b3198ef57c964f))
* Undo previous commit ([`f4c2e74`](https://github.com/imageio/imageio/commit/f4c2e74f45c261c41e50ef97ca201b8239386ff7))
* Bump required pillow version ([`1a4456c`](https://github.com/imageio/imageio/commit/1a4456ced83b71f6c4e47701cbf3669d2dcd6dff))
* Avoid pillow 8.3.0 ([#656](https://github.com/imageio/imageio/issues/656)) ([`abe3cc2`](https://github.com/imageio/imageio/commit/abe3cc262c449f32087274f22fd9d24561194fb3))
* Close request if no backend was found ([`1f8ff6b`](https://github.com/imageio/imageio/commit/1f8ff6b4728385f776b4707471c039dde8efb60d))
* Introduce InitializationError ([`974fdc5`](https://github.com/imageio/imageio/commit/974fdc5cf977d73039b22a60e73195ddc5dc46bb))
* Linting ([`e25f06f`](https://github.com/imageio/imageio/commit/e25f06fa942b7452f34b4c6c983dfccbc12b4384))
* Merge master into feature ([`6576783`](https://github.com/imageio/imageio/commit/6576783456270d024057f280197eec51c9bbf476))
* Instantiate plugins once ([`081f3e6`](https://github.com/imageio/imageio/commit/081f3e6b3740c81484fec92f5e1b13424a406e34))
* Make FITS the preferred plugin for FITS files ([#637](https://github.com/imageio/imageio/issues/637)) ([`6fbab81`](https://github.com/imageio/imageio/commit/6fbab81e7598af847c840c93c9ebec9a94d1f242))
* Remove compromised token ([#635](https://github.com/imageio/imageio/issues/635)) ([`7fdc558`](https://github.com/imageio/imageio/commit/7fdc5585a0b09ca0d4e6c9e08bf1039015ea8bde))
* Get images from imageio not firefoxmetzger ([`9da8339`](https://github.com/imageio/imageio/commit/9da8339fd18dd69c00f9f2eda5dc1b29f421a7cf))
* Throw-away requests for get_reader/get_writer ([`cf83968`](https://github.com/imageio/imageio/commit/cf839683205f409b28e7a17be3580a80be66abb3))
* Black + flake8 ([`53ed8d8`](https://github.com/imageio/imageio/commit/53ed8d823dd4b036e5aebcd2f0529aad67ef3831))
* Test mvolread with mvol image ([`3a03d26`](https://github.com/imageio/imageio/commit/3a03d267e832a57017c376a3c1649c0dd42d3927))
* Investigate pypy failure ([`9d63acc`](https://github.com/imageio/imageio/commit/9d63accc8a587bff2a228c1f69dc89b5004934a4))
* Remove dublicate checks ([`7148fa9`](https://github.com/imageio/imageio/commit/7148fa9fec72b06ac328db7246278e59e40c3d9b))
* Remove dublicate code ([`9a99417`](https://github.com/imageio/imageio/commit/9a99417abaadf0e536ff763d8046baa78fe5c85b))
* Flake8 + black ([`42a02ed`](https://github.com/imageio/imageio/commit/42a02edc6cd2aad51cb67b4782a643fa5fbad870))
* Raise error for invalud modes in py3.6 ([`c91ae9c`](https://github.com/imageio/imageio/commit/c91ae9c400b12932bf213058ab48f9936fff225c))
* Black + flake8 ([`abe7199`](https://github.com/imageio/imageio/commit/abe71996aa240bf01a926e4d0ff14f24194b96e6))
* Pillow changed gif reading. updating test ([`2ebe936`](https://github.com/imageio/imageio/commit/2ebe936872329abc3be7e58b375f3d6e8481cd5c))
* Flake8 ([`6debb11`](https://github.com/imageio/imageio/commit/6debb110685a26899197b8b224cc9d4ff92cee6e))
* Blackify ([`6676a62`](https://github.com/imageio/imageio/commit/6676a628f9cacdcfcffb1fd6b7580c52fc023326))
* New black formatting rules ([#630](https://github.com/imageio/imageio/issues/630)) ([`659f4f7`](https://github.com/imageio/imageio/commit/659f4f7a8844a7d7383d07020bd45512feb02cf6))
* Merge master into branch ([`edad86f`](https://github.com/imageio/imageio/commit/edad86f9b8f20a88a8efa9aa79d2fd170ebfa6d2))
* Make Request.Mode an enum ([#622](https://github.com/imageio/imageio/issues/622)) ([`dc2d06b`](https://github.com/imageio/imageio/commit/dc2d06b2358b6451164961b42a6d2f566fa5169e))
* Fix highlighting of installation command ([#615](https://github.com/imageio/imageio/issues/615)) ([`9df61d2`](https://github.com/imageio/imageio/commit/9df61d23f398904c96c334c67dbf67c655e15c52))
* Remove double import ([`388e57d`](https://github.com/imageio/imageio/commit/388e57d3edb582f6b2e4aadeb97e13b0809d582a))
* Merge master into v3.0.0 ([`7443ffd`](https://github.com/imageio/imageio/commit/7443ffd5fa6d9c0a0566f1830e51ef21ec58ffcb))

### Documentation
* Refactor plugin docs ([#666](https://github.com/imageio/imageio/issues/666)) ([`787db4b`](https://github.com/imageio/imageio/commit/787db4b246c466e05197fc7007922e5dc44e2074))
* Fix typo ([#659](https://github.com/imageio/imageio/issues/659)) ([`bb13525`](https://github.com/imageio/imageio/commit/bb13525f35300e9d924eeb23d05ef3408d1c15fa))
* Fixed Typo ([#653](https://github.com/imageio/imageio/issues/653)) ([`eb24eaa`](https://github.com/imageio/imageio/commit/eb24eaa7fda58331ca28ecbb2709271e9db78e63))
* Update DOI ([#650](https://github.com/imageio/imageio/issues/650)) ([`b4f186f`](https://github.com/imageio/imageio/commit/b4f186f22df4454030060fc0545cd53b85956c44))
* Added missing docstring to function ([`6625430`](https://github.com/imageio/imageio/commit/66254303eea9c4a8ef9075e2e31dc0163955db8e))
* Clarify _missing_ method ([`2fd5116`](https://github.com/imageio/imageio/commit/2fd5116cd5d8ac9b2495ef853a22a46d861744bc))
* Update Website Link ([#634](https://github.com/imageio/imageio/issues/634)) ([`2f058d7`](https://github.com/imageio/imageio/commit/2f058d71251bdb53e91cd92f828ff27dbe5765f4))
* Polish imopen docstrings ([`7052cd8`](https://github.com/imageio/imageio/commit/7052cd83b402efa0fd43540c3400a9aad75a6d76))
* Clarify documentation on .tif handling ([#625](https://github.com/imageio/imageio/issues/625)) ([`68bb515`](https://github.com/imageio/imageio/commit/68bb515e9ba5986a22c44246396071a72ac07575))
* Add repo location to  developer instructions ([#584](https://github.com/imageio/imageio/issues/584)) ([`2ce79b9`](https://github.com/imageio/imageio/commit/2ce79b91c5415dd3069be1050d979a5bfd4245e1))

## [2.9.0] - 2020-07-06

### Fixed

* More robust loading of  FEI SEM data (#529 by jon-lab).
* Fix webcam not working on Win10 (#525).

### Added

* Add a few standard images useful to 3D visualization.
* The timeout used in HTTP requests can now be set with an environment variable (#534 by Johann Neuhauser).
* The DICOM plugin can now used gdcm for compressed transfer formats.
* Better support for itk/sitk plugins (#530 by Jonathan Daniel).
* Test coverage and CI for ARM (#518 by odidev).


## [2.8.0] - 2020-02-19

(skipping version 2.7 to avoid confusion with Python v2.7.)

Mentioning here for completeness: imageio-ffmpeg 0.4.0 was also recently
released, which fixes several (stability) issues for video io.

### Fixed

* Better support for reading from http (some formats needed seek, we now deal with that).
* Make `Reader.__len__` work again when length is inf (stream/unknown).
* Set `-framerate` input param for ffmpeg when using webcam, fixing webcam support on macOS.
* Fix for handling TIFF predictor value of 1 (NONE) (by Milos Komarcevic).
* Fix false-positive zip detection (by Vsevolod Poletaev).
* Fix SPE filesize check for SPE v3 (by Antony Lee).
* Fix that SPE plugin failed on spe3 files with dtype uint32 (by Michael Schneider).
* Fix deprecation warning for numpy.

### Added

* Expose SPE3 xml footer (by Antony Lee).
* Expose TIFF predictor tag for reading and writing (by Milos Komarcevic).
* Improve error message regarding modes.

### Removed

* Drop support for Python 2.7 and Python 3.4.
* Drop support for AVbin, use ffmpeg instead.


## [2.6.1] - 2019-10-08

* Fixed potential error when creating a new appdata directory.


## [2.6.0] - 2019-10-07

This will likely be the last release to support Python 2.7.

Fixed:

* Fixed a security vulnerability for Windows users that have dcmtk installed,
  and where an attacker can set the filename.
* Fixed bug in ``image_as_uint`` (#451 by clintg6).
* Fix that only one webcam could be used when two cameras are connected that have the same name.
* Prevent paletted image with transparency to be converted to grayscale.

Added:

* Optimise 16-bit PNG write performance for newer versions of Pillow (#440 by Ariel Ladegaard).
* More flexible setting of memory limit in ``mimread`` and ``mvolread`` (#442 by Chris Barnes).
* Support for ASCII PNM files (#447 by Tobias Baumann).
* Improved support for JPEG2000 (can now provide parameters) (#456 by Pawel Korus).
* Added support for compressed FITS images (#458 by Joe Singleton).
* Improve imageio import time by avoiding pkg_resources import (#462 by Mark Harfouche).
* Added example for compressing GIFs using pygifsicle (#481 by Luca Cappelletti).


## [2.5.0] - 2019-02-06

The ffmpeg plugin has been refactored:

* The core has been moved to a new library: imageio-ffmpeg.
* That library provides platform-specific wheels that includes ffmpeg,
  so just ``pip install imageio-ffmpeg`` instead of the download step.
* Note that this new library is py3k only.
* Termination of ffmpeg subprocess is now more reliable.
* The reader of the ffmpeg plugin now always reports ``inf`` as the number of
  frames. Use ``reader.count_frames()`` to get the actual number, or estimate
  it from the fps and duration in the meta data.
* Removed ``CannotReadFrameError``.

Other changes:

* The avbin plugin has been depreacted and will be removed in a future version.
* Imnproved speed for PIL and FFMPEG plugsins by avoiding memory copies.
* Update the included tiffile library.
* Support for SimpleITK.
* Speed up tiffile plugin when writing to something else than a filename.
* Fix that writing to a file object would not work for some plugins.
* Can now pass image data to the write functions as anything that resolves to
  a numpy array with a numeric dtype.
* One can now read from a memoryview.
* Fix error related to paletted BMP with the Pillow plugin.
* Improved logging.


## [2.4.1] - 2018-09-06

* Fix installation issue on flavors of Ubuntu 14.04 /w Python 2.7  (#378).
* Use `np.frombuffer` instead of `np.fromstring` in some cases.


## [2.4.0] - 2018-09-06

* Renamed ``Image`` class to ``Array`` and add documentation for this ndarray subclass.
* Reading from HTTP and zipfiles has been improved and better documented.
* Improvements to reading and writing of Tiff metadata (by Lukas Schrangl).
* Better dealing of tifffile dependencies on Python 2.7 (#330 and #337 by Chris Barnes).
* Reader for the SPE format (#358 by lschr).
* Better termination of FFMPEG when reading from webcam (#346 by Dennis Vang).
* FFMPEG support for reading 16bit videos (#342 by Peter Minin).


## [2.3.0] - 2018-03-20

* Console entry points for binary downloads (by Paul Mueller).
* Dropped support for Python 2.6, 3.2 and 3.3.
* Reading images from a url can now also have "suffixes" like "?query=foo".
* The ``mimwrite()`` and ``mvolwrite()`` functions also work with generators.
* Fix rounding of float data.
* New Lytro plugin (by Maximilian Schambach).
* New plugin based on BSDF format (for images/volumes and series thereof,
  including support for random access and streaming).
* TIFFFILE update to latest ``tifffile.py`` implementation.
* DICOM fix that could fail in the presence of a directory.
* PILLOW improvements to API to provide same functionality as Scipy's ``imread()``.
* PILLOW fix for Gamma correction (#302).
* PILLOW now allows JPEG images to be read from a url.
* PILLOW fix determining of grayscale in 1 bit paletted images.
* FFMPEG improved device name parsing (by Dennis van Gerwen).
* FFMPEG now allows more control of position of extra parameters.
* FFMPEG improved parsing of fps from ffmpeg info.
* FFMPEG reader allows has ``fps`` argument to force reading at a specific FPS.


## [2.2.0] - 2017-05-25

* New format for grabbing screenshots (for Windows and OS X).
* New format for grabbing image data from clipboard (Window only).
* Multipage Tiff files can now be read using ``volread()`` to obtain the image
  data as one array.
* Updated the ffmpeg executables that imageio provides.
* The ffmpeg format can now also use the ffmpeg exe provided by the ffmpeg
  conda package (``conda install ffmpeg -c conda-forge``).
* Fixes to ffmpeg format in general.
* Improve docs and rounding in animated GIF duration.
* Fix for setting number of loops in animated GIF.
* Fixes for transparent images in Pillow.
* Fixes for float indexing that is disallowed in new Numpy (Freeimage plugin).
* Fix for using missing ``close()`` on Pillow images.
* Updated version of tiffile plugin.


## [2.1.2] - 2017-02-02

A bugfix release:

* Fix animated gif writer that was broken in newer Pillow version.
* FFMPEG plugin improvements: more reliable fps detection, can deal
  with missing FPS, more reliable subprocess termination,
* Mimread allows a few missing frames to better deal with certain video files.
* Allow question marks in url's.
* Allow Pillow plugin to read remote files by "enabling" ``seek()`` and ``tell()``.
* Use invoke to run development tasks instead of custom "make" module.


## [2.1.1] - 2016-12-24

Minor improvements related to Debian packaging.


## [2.1.0] - 2016-12-22

* Standard images now have to be specified using e.g.
  ``imageio.imread('imageio:chelsea.png')`` to be more explicit about being
  a special case and potentially involving a download.
* Improvements and fixes for the ffmpeg plugin (including improved seeking).
* Several tweaks to the tests and setup script to make it pass the Debian
  build system.


## [2.0.0] - 2016-12-10

This release introduces a new plugin based on Pillow, which will take care of
the "common formats" like PNG and JPEG, which was previously the role of the
FreeImage plugin. The latter is still available but the FreeImage library
is no longer distributed by default.

* New Pillow plugin to privide the common formats.
* FreeImage plugin gets lower priority w.r.t. resolving a format.
* No more automatic downloading of libraries and executable (for
  FreeImage, FFMPEG and AVBIN plugins).
* Pillow plugin comes with a format to read/write animated GIF to supersede
  the one provided by FreeImage.
* Various improvements/fixes to the ffmpeg plugin.
* Fixes and improvements of the DICOM plugin.
* Better support of exr images via FreeImage (by Joel Nises).
* New FEI format (for images produced by the FEI SEM microscope).


## [1.6.0] - 2016-09-19

* Got rid of Lena image because it can be regarded offensive and is not (explicitly) publicly licensed.
* Fix issue with ffmpeg reader being slow on particular systems (#152).
* Tiff plugin updated.
* Add Tiff resolution support (Antony Lee).
* Support for 16bit PNG's (#150, by OrganicIrradiation).
* Fixes to ffmpeg plugin (#149, #145, #129).
* Fix in using IMAGEIO_FREEIMAGE_LIB (#141, by Radomirs Cirskis)
* Better ffmpeg verbosity and exe detection ( #138, #139, by Tim D. Smith).


## [1.5] - 2016-01-31

* Freeimage conda package (in main channel) is updated and works on all
  major OS's.
* Conda install imageio!
* Fix bug where the ffmpeg plugin fails on certain video files (#131).
* Fix how dicom uses dcmtk for JPEG compressed files.


## [1.4.0] - 2015-11-18

* Various improvements to the ffmpeg plugin.
* New tiffile plugin that should support most scientific formats.
* New simpleITK wrapper plugin.
* New gdal plugin.
* Freeimage plugin can load freeimage lib provided by conda.
* Dicom plugin improved handling of compressed files.
* Most plugins adopt lazy loading to keep imageio lean, fast, and scalable.
* We now build wheels for Pypi.
* Travis also tests Python 3.5.


## [1.3.0] - 2015-07-02

This release features several fixes and small improvements, especially
to the ffmpeg plugin.

* Fix 'FrameTime' in first frame of GIF image (#90)
* Fix that writing video could freeze on Windows (#84)
* Fix that ffmpeg process was sometimes not closed correctly (#79)
* Also protect user from clogging the machine for mvolread (#89)
* Better support for platforms other than Win/Linux/OSX (#87 )
* Support for reading from webcam on OSX (#83, #85)
* Support for dpx via the ffmpeg plugin (#81)
* Support for wmv via the ffmpeg plugin (#83)
* The ffmpeg plugin allows specifying pixelformat. The new default is
  more widely supported (#83)
* Allow passing additional arguments to ffmpeg command (#83)
* Quality of ffmpeg output now set via quality param instead of bitrate (#83)
* Imageio now has a few (documented) environment variables to specify
  the locations of plugin libraries/exes (thus preventing them from
  being automatically downloaded.


## [1.2.0] - 2015-02-23

Basically a hotfix release. But some new features were introduced.

* Fixed that pip-installing would put README.md and other files in sys.prefix.
* The used ffmpeg exe can be overridden with an environment variable
  'IMAGEIO_FFMPEG_EXE'.
* Relative paths work again.
* FFMPEG plugin moved to correct timeframe when seeking (thanks Zulko)


## [1.1.0] - 2015-02-04

Imageio is now a dependency of `Moviepy <https://github.com/Zulko/moviepy/>`_,
which exposed a few issues to fix. Imageio is now also available as a
Debian package (thanks Ghislain!). Furher, we tweaked our function names
to be cleared and more consistent (the old names still work).

* All ``Xsave()`` functions are renamed to ``Xwrite()``.
  Also ``read()`` and ``save()`` are now ``get_reader()`` and ``get_writer()``.
  The old names are available as aliases (and will be for the foreseable
  future) for backward compatibility.
* Protect user from bringing computer in swap-mode by doing e.g.
  ``mimread('hunger games.avi')``.
* Continuous integration for Windows via Appveyor.
* All imports are relative, so imageio can be used as a subpackage in
  a larger project.
* FFMPEG is the default plugin for reading video (since AVBIN has issues).
* Better handling on NaN and Inf when converting to uint8.
* Provide dist packages that include freeimage lib and a few example images.
* Several changes to ease building into Debian package.
* Fixed segfault when saving gif
  (thanks levskaya, https://github.com/imageio/imageio/pull/53).
* Don't fail when userdir is not writable.
* Gif plugin writer has fps param for consistency with avi/mp4 etc.


## [1.0.0] - 2014-11-13

In this release we did a lot of work to push imageio to a new level.
The code is now properly tested, and we have several more formats.

The big changes:

* Many unit tests were written to cover over 95% of the code base.
  (the core of imageio has 100% coverage).
* Setup continuous integration (CI) using Travis.
* Imageio now follows PEP8 style guides (and this is tested with CI).
* Refactoring of the code base. Resulting in a cleaner namespace.
* Many improvements to the documementation.

Plugins:

* The FFMPEG format is now well supported. Binaries are provided.
* New AVBIN format for more efficient reading of video files.
* New NPZ format that can store (a series of) arbitrarily shaped numpy arrays.
* New SWF format (shockwave flash) for lossless animated images.
* Improvements to the GIF format. The GIF and ANIGIF formats are now merged.

Further:

* New simple website to act as a front page (http://imageio.github.io).
* Compatibility with Pypy.
* We provide a range of :doc:`standard images <standardimages>` that are
  automatically downloaded.
* Binaries (libs and executables) that plugins of imageio uses are now
  downloaded at runtime, not at build/install time. This simplifies
  things a lot.
* freeimage plugin now fully functional on pypy
* Added utilities for developers (run ``python make`` from the repo root).
* PNG, JPEG, BMP,GIF and other plugins can now handle float data (pixel
  values are assumed to be between 0 and 1.
* Imageio now expand the user dir when filename start with '~/'.
* Many improvements and fixes overall.


## [0.5.1] - 2014-06-23

* DICOM reader closes file after reading pixel data
  (avoid too-many-open-files error)
* Support for video data (import and export) via ffmpeg
* Read images from usb camera via ffmpeg (experimental)


## [0.4.1] - 2013-10-26

* We moved to github!
* Raise error if URI could not be understood.
* Small improvement for better error reporting.
* FIxes in mvolread and DICOM plugin


## [0.4.0] - 2013-03-27

Some more thorough testing resulted in several fixes and improvements over
the last release.

* Fixes to reading of meta data in freeimage plugin which could
  cause errors when reading a file.
* Support for reading 4 bpp images.
* The color table for index images is now applied to yield an RGBA image.
* Basic support for Pypy.
* Better __repr__ for the Image class.


## [0.3.2] - date unknown

* Fix in dicom reader (RescaleSlope and RescaleIntercept were not found)
* Fixed that progress indicator made things slow


## [0.3.1] - date unknown

* Fix installation/distribution issue.


## [0.3.0] - date unknown

This was a long haul. Implemented several plugins for animation and
volumetric data to give an idea of what sort of API's work and which
do not.

* Refactored for more conventional package layout
  (but importing without installing still supported)
* Put Reader and Writer classes in the namespace of the format. This
  makes a format a unified whole, and gets rid of the
  _get_reader_class and _get_write_class methods (at the cost of
  some extra indentation).
* Refactored Reader and Writer classes to come up with a better API
  for both users as plugins.
* The Request class acts as a smart bridging object. Therefore all
  plugins can now read from a zipfile, http/ftp, and bytes. And they
  don't have to do a thing.
* Implemented specific BMP, JPEG, PNG, GIF, ICON formats.
* Implemented animated gif plugin (based on freeimage).
* Implemented standalone DICOM plugin.


## [0.2.3] - date unknown

* Fixed issue 2 (fail at instal, introduced when implementing freezing)


## [0.2.2] - date unknown

* Improved documentation.
* Worked on distribution.
* Freezing should work now.


## [0.2.1] - date unknown

* Introduction of the imageio.help function.
* Wrote a lot of documentation.
* Added example (dummy) plugin.


## [0.2.0] - date unknown

* New plugin system implemented after discussions in group.
* Access to format information.


## [0.1.0] - date unknown

* First version with a preliminary plugin system.
