# Prospective exact inherited-terminal adjudication registration

Prepared before the separate qualifier executes; qualification and implementation
acceptance remain pending. PDR-0161 follows the approved E4 path. Both original
literal commands remain failed, including their unchanged reports and dirty flag.
No oracle source, frozen input, matrix or reward-stream allowance is changed.

Candidate: `462e8a3980845d76e7987cfea67fb63432bcb847`.
Checker SHA256: `05fa08a7d36fdc0222339fc23f867c971d221a0270b41ab0784f21ca86397a27`.
Completed specification SHA256: `471412bcd3016b9a76bc739caf455386b3214729734b7229fb29fc403ea512da`.
The complete bytes below freeze 182 evidence bindings (157 originals plus25 final),
434 original config bindings, seven literal float32 reward coordinates, all full
trace/source/event/component checks, and42 required corruption controls.
Astra has approved the method and checker structure; final fence approval is
required before the root GO. This registration itself reports no passing gate.

## Frozen completed specification

```json
{
  "format_version": 2,
  "status": "FROZEN PROSPECTIVE FINAL SPEC; QUALIFICATION REQUIRES ROOT GO",
  "source_shas": {
    "parent": "880f9c90f65aa646a0da04d7ca2ef92e48f85caa",
    "E2": "10cfc83495146f49d8fd8aeb7f3ba149ab087f54",
    "E3": "904f166ad17f201619e60e6284fd1e41c492c77b",
    "candidate": "8e3ca306d6f615bd272bb1c8d51b071b74686877"
  },
  "source_bindings": {
    "parent": {
      "sha": "880f9c90f65aa646a0da04d7ca2ef92e48f85caa",
      "source_root": "/home/john/hamlet/.worktrees/episode-lane-implementation/runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/sources/parent/src",
      "src_tree": "7fefe5efb599515c919bdb9826ce1d6667fe5f8b",
      "archive_sha256": "f4bba876915f9110faca1aa49baddff015b0b2083b3c56acf38f9b5fe6a90089",
      "closure": {
        "src/townlet/__init__.py": "802316b1b3acf1050d09751438d90c55ea11466a35a233fbbd2c1574c89ff80b",
        "src/townlet/agent/__init__.py": "7c66a7875664264fa84f1ced05578f2aa667b2f972694807d30efc250cf0c13b",
        "src/townlet/agent/loss_factory.py": "34ae008c6df833118906421ade7421479272418999b265fd19382766800d3de5",
        "src/townlet/agent/network_factory.py": "976ff4f761c65981ce0f35812379abbdef940e81bed21e8f2715c2df02efb6fd",
        "src/townlet/agent/networks.py": "a318511db13002a0b222a1741b1c90af49d333ed129fbf15338193ce28cac7ca",
        "src/townlet/agent/optimizer_factory.py": "56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d",
        "src/townlet/agent/token_diagnostics.py": "5d6c4ed12a053167e5caf137be5537e4dc1de727216fe9bff36ac5a899c2cd0d",
        "src/townlet/agent/token_input.py": "2aaab1b6d524ec5371e1e3503c936c1359d2a241826315afdd088cfbb6d44ba3",
        "src/townlet/config/__init__.py": "f6a870d05e3f901d6ecfa39bbad890d14cf529172a250ce821005424e0ba4f9b",
        "src/townlet/config/actions_config.py": "bc4cfeead60fc22f7cd29204bda07e23a37b385fd15e86f28ac5e5df5c44350c",
        "src/townlet/config/affordance_masking.py": "d098f6c2ccc3110b8d71ba9896faf1eb2b2686eb24fc98d05412b20aa29a45e4",
        "src/townlet/config/affordances_v2_config.py": "57f3510259c016fdc0d063775752ab2afed4402ed72509e7403f0ff52a30c379",
        "src/townlet/config/bars_v2_config.py": "e675ee8693ab60641e5a71f738f8a68092549d6a5ff4e20605878eb2c2df91a2",
        "src/townlet/config/base.py": "77d39a08edd7045214b907b0ec156d9ef160669a57d57b9fa5537c9235571d39",
        "src/townlet/config/brain_config.py": "129e72918dc1753a25e204761ebff2978a0a28a2af226af0536b8ec2331834ee",
        "src/townlet/config/capability_config.py": "2761ad15f3bff36313a3d81a592f391faa0dfc8050315d58eb0b283c9162c579",
        "src/townlet/config/curriculum.py": "1ab88dced36a1277e0e161e55bd6d9e1d736c0b8e6be723fddfa8a30d97db393",
        "src/townlet/config/curriculum_config.py": "32f62734b99575a1d19f20f9d113e56e70960ec722e4a39a521c208edcf56a7c",
        "src/townlet/config/drive_as_code.py": "5b1a00313c39e695477d65703dd51b75e607b748d8b95d9cdd11d74c3a8b8b40",
        "src/townlet/config/effects_config.py": "f53679ccbf8ba85a27d3dfa92c15bf3944a1ded00d660793c77c5e1c01af1de3",
        "src/townlet/config/environment_config.py": "03de4c4007b1bcf3ce86a7a974d665cb887236a3f8e4d6fc808f6700ac8198ef",
        "src/townlet/config/experiment_config.py": "d4d7013fc8eeda910448aa4878cf3dc730f79f24b1d875629a1f62c1e4bb4ac6",
        "src/townlet/config/exploration.py": "50c9b69a287c414401ecff7fdf1af1661c18a5c0cbea822692429efdab251afb",
        "src/townlet/config/interaction_type.py": "dc08d3b6b8ef7e3ad0a94ef7c2a688d27cacd802c87fe9901edad6865d4a0b6d",
        "src/townlet/config/items_config.py": "2af1223f6f01f4a32d50a3f06aa91d32893e4783ee0cb62be439dccfefc8060b",
        "src/townlet/config/presentation_config.py": "9f44315a53bb1ae922335068c5f78fb1d8a646e9924124479b365b0cf4bbd08a",
        "src/townlet/config/stratum_config.py": "08473a0f3052f06ffb74ec85026a1deb91843206e9d22fb0487f109281f659a4",
        "src/townlet/config/training_v2_config.py": "996b508557aa1378642c7f455f5a5fb7a5961337d9a3fb9fc9582b3c800b07b4",
        "src/townlet/config/transition_rules_config.py": "8bfab492badfea9e24da5f4ae2cbe09629b031240036db99ab1ca16c1cf87751",
        "src/townlet/config/variables_config.py": "eb895c51d9b1983f7db539dbc949b33818fc1abf8de6190061dcfdbac565a4c9",
        "src/townlet/curriculum/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/curriculum/adversarial.py": "8ce48905b6163d25ff98f692af7986447245cc29eba47bcc248f10e4f4b8cf8b",
        "src/townlet/curriculum/base.py": "04bfb42f3b5d4faa3728be82d6c476448011fdb0c63788a24296839375b1ae26",
        "src/townlet/curriculum/factory.py": "82f464d5a3dfaaaca4e06cd1fffb7f2ddb5c2646ef62524214598d236846aabe",
        "src/townlet/curriculum/static.py": "4bce47073d50962defe1c405ca4a5fbda480e8321e2e38ff8e3558d7fafbf1be",
        "src/townlet/demo/__init__.py": "5237c34f4b094f949ae3d4983fc3edd057dd88329f64ca90d7c8d6ac3b150b0a",
        "src/townlet/demo/database.py": "945ea042fdacc9b265ce6a2e4b4d62fd9b876c816c6a00dd29df94d99d2bb082",
        "src/townlet/demo/live_inference.py": "5c8023d89312712587ad14c448659133a762ed62e2c38f423a2c474fa89c83f9",
        "src/townlet/demo/presentation.py": "81fd5a91b2a8bcc5dc0cae06c02892acd52fbde11a7dcfc95a11a62cf60b74d8",
        "src/townlet/demo/runner.py": "71c3c1b8b326a55ab78b4b19ee5f843e120919a41038043df608fd05b490add3",
        "src/townlet/demo/unified_server.py": "7ab22810e77496e3bfc310046adb69e00155119d035d914bdaaa3d070c9e4f37",
        "src/townlet/determinism.py": "73b8cd748bf1d495d0dfa22842e85c2e5a52421bd3081afbfd401eb0c0f14244",
        "src/townlet/effects/__init__.py": "94af62ccbac0dc840e3b2147ad7cdfd5d694961945ff478863cc12c3bec61b49",
        "src/townlet/effects/admission.py": "09407fc85cda41afea750f858dd2c0235af5d03064a4094d82b3bb1cee7bf3f9",
        "src/townlet/effects/affordance_identity.py": "bc073b35cb8a9bba55d5e42acca879838a9cad532673f98b40abea790fd1fb31",
        "src/townlet/effects/catalog.py": "d92e7e8d6a229643758156d35b1583a23bb327b93b5722b426bb2766b759ab48",
        "src/townlet/effects/collections.py": "686a5c6118177069a614bc9c451be830ad6ba92d548b56d2898cd6c30c0aaa81",
        "src/townlet/effects/compiler.py": "09d377f119427525153da3086c52064ec6fe9cf69fea429a5dddea61ada7064f",
        "src/townlet/effects/context.py": "ed23cbdf16734882dd5770f67fc2b34403378b332f5bdbf917559096947f3404",
        "src/townlet/effects/executor.py": "3cb5f6adc251469aaf7f6caddaa9b538a5a9d1807ea4e90cdf4efb0c2ee82d9a",
        "src/townlet/effects/manager.py": "dbfac81773c3b9876e3db1d036d71d510451a2476b446240f6649497f1203777",
        "src/townlet/effects/parser.py": "8219058196d705bf4b236bdae944a0e5fc6127d8040ba00c7b98bb53ae5a1bb0",
        "src/townlet/effects/scheduler.py": "4973ad2e614669f92b9334d720dcd9317c07569c8247c03b781f6c631e6d26c7",
        "src/townlet/effects/schema.py": "7d639c4824813c633935a770c0358a0ad53af6e8cfb336a96041376046f0bdcf",
        "src/townlet/environment/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/environment/action_builder.py": "2c1269579f0f17f88681be3811b2021bad4931c658a09767a035e37243ebf8bf",
        "src/townlet/environment/action_config.py": "42d966352145d8a6410349e429d3e1d8d687e78ab8f91372de6645520aeaf7d0",
        "src/townlet/environment/action_executor.py": "5c7b350a34ac78e193e63b977e73c3c246b46547d8cf6f3e46b501e765d969bd",
        "src/townlet/environment/action_labels.py": "c9b47042502e4491845125a0c14af6643f1e10174492ebdc33d2e043e5237b50",
        "src/townlet/environment/action_mask_builder.py": "02d57542a4fa340a1e69f819117c364366e7e1c947ebbf0d63b7663749293293",
        "src/townlet/environment/affordance_engine.py": "706a981bb78f3eb216e83b5e615180174dc7d2f2aa72e208b783c5fbe601fae3",
        "src/townlet/environment/affordance_layout.py": "af5474a54298246ab0d371382da7565c16c436802bc967233b2ac586272ac891",
        "src/townlet/environment/dac_engine.py": "c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6",
        "src/townlet/environment/env_factory.py": "ab9489d854fba3b644439b19a964190e78302a78132646132921c2ece7f0d232",
        "src/townlet/environment/null_managers.py": "670489567be0de077ab35f45b0536b964f521fcc263ef679491fc4a2348cb7d2",
        "src/townlet/environment/observation_encoder.py": "d7e31d1b35e81091efc8a87789864323f95779f97e4f1f3ba196a9cd76509054",
        "src/townlet/environment/reward_calculator.py": "6db3a8fb1fe8e3e29201bd89ca1b993995a35c797e3c3323bf17a07210a6b16b",
        "src/townlet/environment/substrate_action_validator.py": "c81ae44eddc072499c3f7d783149ca142012e671a4ea53f6f0efc8ec7908ec41",
        "src/townlet/environment/token_publishers.py": "0c9104f6f4da839ae616203f72cfd9e011923dc118c0ecf4fc8976c4ac31ac28",
        "src/townlet/environment/vectorized_env.py": "403945f1dbb9f26e40f77ce5557bcd48b59559b98f30a4e13611a264ad7d3093",
        "src/townlet/exploration/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/exploration/action_selection.py": "c5362a5078c7ecce9dfac0727364a346988054e83228975abaf0939369d48d3e",
        "src/townlet/exploration/adaptive_intrinsic.py": "80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9",
        "src/townlet/exploration/base.py": "49a9a23c2dcf3705a7712fc0bc74d11aa4b30aeee8fba1d0f87a609e05fbd1ae",
        "src/townlet/exploration/epsilon_greedy.py": "f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059",
        "src/townlet/exploration/rnd.py": "58200c260ab0535319b2747b0ff73368dbf50667a9c081de3de23c9df272059d",
        "src/townlet/items/__init__.py": "53401e4dcdcdf71a2f0d6bc1c98e24f3488b0a61da8b0ffb737b96465298550e",
        "src/townlet/items/action_handlers.py": "76c9a2d1a682d17be718a20e05ec432c9b5a3bf942ec0aca14035442d25c4359",
        "src/townlet/items/instance.py": "c9672879907eb1f9f1d94d7817683b51886b78712cfc819d0b9e976f5a2cbe51",
        "src/townlet/items/inventory.py": "175036c8faea2a53f34010276c5e4d7257e836c9420d15886d6b66e8dea31c35",
        "src/townlet/items/manager.py": "69a626220c46d69521e7997a24d453cdbd8fb08fd170ef81a504205792245fc6",
        "src/townlet/numeric.py": "96c53eac046b9268732e794c2375b99be6506f97f51a68465f8318d6bf52865d",
        "src/townlet/oracle/__init__.py": "aa1cb6cc0e190dfea45cea6f41df35f5cb7cef8292343d83e843610c41aa86b1",
        "src/townlet/oracle/driver.py": "f69ea42c0313b85bb5c4b5b9f668a4502e4988882485302438181edeb979bfab",
        "src/townlet/oracle/harness.py": "0896facbf37cfca897f11242feab2dc1c35041b1363603cf8947e76e7719f0d8",
        "src/townlet/oracle/matrix.py": "81bfe561f19cae191b832995d97cc20dd17d044cbc67fc37330f48ccdaced865",
        "src/townlet/oracle/trace_io.py": "bd7f1136ad29572152b1fee9084566e34982c4912f5c918cc14300fd35f3472c",
        "src/townlet/population/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/population/base.py": "b10f0e4ed767d91a487b9447a45bd82a2bf80a0696bf29fd4335a0728911b392",
        "src/townlet/population/runtime_registry.py": "1425748c6abbb01aff170be023547f5a5c11eb35c92d29ea416bbf848b461f50",
        "src/townlet/population/vectorized.py": "53ed3e6414fa45a5b677d318f97660195390bcb8f3c64b88b429ec23e16b2f1a",
        "src/townlet/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "src/townlet/recording/__init__.py": "141d8edde1c83f709f01f2c20878caef1ce2e77c9922280b13bff25fb2d24231",
        "src/townlet/recording/__main__.py": "b4ef951f6f24f434efb6d206eb617923fec08866f34f30aa54de1fd4d26aa7a2",
        "src/townlet/recording/criteria.py": "bcfb3eacf7ea72d1148958d4d3a3e56032dad2adbc7a0c2ce7a72b11e0185191",
        "src/townlet/recording/data_structures.py": "ac0ee45925a581c594add3757883070984d5b8842970cd5ef802903d37dc8940",
        "src/townlet/recording/recorder.py": "9d797ce3a295d0bb4cbb3f4a376cdc1d62d0965daf05704d09d088c53fdb90f0",
        "src/townlet/recording/replay.py": "44e6f79f9f2635420281d3160f2e792f78b10f9a807200600c3100af8837bef1",
        "src/townlet/recording/video_export.py": "057b129fe3a634260568998c57c3db58ccbdd870f544a9dff15add971614cf56",
        "src/townlet/recording/video_renderer.py": "650eedd5ac181a505d6bedc7628cf12245cbd5564cff19cf809106aba6246f88",
        "src/townlet/substrate/__init__.py": "a6f4a318bdfa4acd63a57c99159eff35091fb599542e0e1cc269df66f859d018",
        "src/townlet/substrate/aspatial.py": "bc4d3936b82946e32183e03a9fe9e0965883fa0fa70fea1382c77f471706b167",
        "src/townlet/substrate/base.py": "f9aee0e7fd64451778b025b7f747be86f4da46146bf8d83c94ae39ba39af4700",
        "src/townlet/substrate/continuous.py": "b310dd8df724fe41e01d9636261b665ee9e10474adc8d5418ed00a7c0d4bdac9",
        "src/townlet/substrate/continuousnd.py": "75b2bf30dcf2b2a35fcfc550bbefdcfb683282b7b791d55a15d3577b46d79312",
        "src/townlet/substrate/factory.py": "f1f58a457341a50e99ff8ea0d82f325b921a8c72a0fd2f0ba2e0b620ccadc918",
        "src/townlet/substrate/grid2d.py": "9f264b90cc15806210e26ba7f91d52be3e28f54d2dd570b775332497bd715d74",
        "src/townlet/substrate/grid3d.py": "c5416e5e5c4338f49ea521ea1a7a979f205f39bba757488990f7466ab7da859f",
        "src/townlet/substrate/gridnd.py": "c4fe656c20c53406d90c12f45069b6a4818ce40f0dd41989e7ae8dda5880fcae",
        "src/townlet/training/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/training/checkpoint_utils.py": "e1103a54385cf3aa06c291b168eb82396a7d19a5fe798d5511aa86e73cdd8efa",
        "src/townlet/training/prioritized_replay_buffer.py": "0248df10333845fd2498d10c2cfb9b59dabcce8c5e8f91f9e645bf9782f4c61c",
        "src/townlet/training/replay_buffer.py": "a1e6f7e43e71c233635a458bc6c01179f15ee0ce922bb02dfce4b4d7624f679c",
        "src/townlet/training/sequential_replay_buffer.py": "6c0b0d644677a6171f03e2ad62b8ab7b99669e401ac630bb2ea2106828e628a7",
        "src/townlet/training/state.py": "a9e88c8977081c1ad9abbc3d85d260f61139a5257894e1900770447bb9f061b0",
        "src/townlet/training/tensorboard_logger.py": "932c7bea6b6e705620a66e756dfa320d01496297f8a1b158c600eeed31474c4d",
        "src/townlet/universe/__init__.py": "f5f10ad3274dfc76983223297f2bc6c47bd7632d8a717e7f5a0f1bee2365c54d",
        "src/townlet/universe/__main__.py": "79026c2399e34a24b34270a69963f98961adbfb04a4cbb3466e66766579ed8d4",
        "src/townlet/universe/compiled.py": "b8ec290f8960bca25998927a42aa2f49c9c8f62ea239874a6e1dbde207aa95d9",
        "src/townlet/universe/compiler.py": "2b7bda405c5cddb7c571f8c0061afcc2a7f7e317b4c4a2609d84d267fb615c64",
        "src/townlet/universe/compilers/__init__.py": "22a0b17fa71b9bb29e4447227b80e9782107dcc95e557cc96e65fe67513c193e",
        "src/townlet/universe/compilers/actions.py": "68a7cf86d2d0e229bbe333ad223531343d3dee51ed72d9c021827754680c94ef",
        "src/townlet/universe/compilers/effects.py": "8f7f8d5b1532e559622ded012ce636cfb892d3ce60074a9fa90e1686d9a59b64",
        "src/townlet/universe/compilers/metadata.py": "02f80e102cd5c897d69fa202a32d7c5fcb92c516bed1d610401ecaf8029923d7",
        "src/townlet/universe/compilers/observation.py": "d5bcf686e15cef0e0ac17f9249872d87a84a0f9e3d2cb210709cf9d10e0a235e",
        "src/townlet/universe/compilers/optimization.py": "9cde440bf462cea96115f6131555c3426eda58036a88a23eb14827de95d0d406",
        "src/townlet/universe/compilers/vfs.py": "eb56da5e8b6e2f41c3f3cbce2ae73b4426433294d81e58ec373b2a75cdf6af6a",
        "src/townlet/universe/declarations.py": "be55efed027b2853a643b958c4a27ead1bd5d1092f26f4cbbdd3ffa6e4005f3f",
        "src/townlet/universe/dto/__init__.py": "e860d56790f1db0ba91ed0380d6c11ad0ca4ef993a6ecdcd76597d3dda7f124f",
        "src/townlet/universe/dto/action_metadata.py": "8c62dafbb4ffb275335c56366e4db22b911050cd446eea0ecfc3ea0a02dbca2c",
        "src/townlet/universe/dto/affordance_metadata.py": "8807059550a2fec1866739869468203c5c77a057eb723a094f31876d9e5f8629",
        "src/townlet/universe/dto/meter_metadata.py": "fbcd7146b0434ac23b91bc1a97492d8ed5c4de7fb9a88f21bcb748664b06a419",
        "src/townlet/universe/dto/token_spec.py": "44e867ea6cc6789a821618d1cd57eec1955bd52ff872922f15c7a98e3257f88a",
        "src/townlet/universe/dto/universe_metadata.py": "85f873e0fc11c784eed830f85f1808f76d7182f52980c89a0b43219073cc5ccd",
        "src/townlet/universe/error_codes.py": "ad49a82718fb7669bec8d4f5a8a43214398e7747173133d896f08c16d412b971",
        "src/townlet/universe/errors.py": "4f37e39c8eff21de3d202b08a099c12cf084a90bb7f8f6f04d7f103a517da02a",
        "src/townlet/universe/loaders/__init__.py": "12803c85f26b3183619cd987ba311f6cde3eab3b31e9899c955b6d9bd584b9a7",
        "src/townlet/universe/loaders/preflight.py": "7fc16741252e0bf6dd0a3fb68f9d492b8c18d1c03912a68fea748ef127bc3435",
        "src/townlet/universe/loaders/v21.py": "84a8543269af6cdbc9bbf79506a5ad79b9363f620501d387721e2eae62f56be2",
        "src/townlet/universe/optimization.py": "bba8c2c7fb2893096030f4a5e5ce89122e2d97a12535e10fdd6b96629be98aef",
        "src/townlet/universe/pipeline.py": "553db4b3d018d2f198fc0d2717ba53209ed5d65ab857c1eeb4358173f4f43768",
        "src/townlet/universe/raw_configs_v21.py": "7f370cb4370b59a3e6a590b9e94c75a7b0abc7cd3d3e9615fe39fa9c318834db",
        "src/townlet/universe/source_map.py": "70daa49af10108b45bf61df6fc471c2b75c3b22b816c8dfecf8057792812b3ec",
        "src/townlet/universe/stages.py": "7edd5fbfc98901b38e05b1eac0debb1dbec7e67dac17075495cdf5d4f77d84d9",
        "src/townlet/universe/symbol_table.py": "6342fef237fb321d8acf758da73434cd8a0da42e0ef5d5a055193819ef480e41",
        "src/townlet/universe/token_hashes.py": "996866109a60b84b9f3b0fc8e1cb0e3da622f13cf3be03f458654213b2cd24ae",
        "src/townlet/universe/validation/__init__.py": "c6c1f481cc1751e1f311c85ac96a735a3a18e0e4fdecaceebdbebd0c5d4be11b",
        "src/townlet/universe/validation/feasibility.py": "a8c1720c04a209c2256628792bdd7529dbede3fc9229ecdf1483ec9b17e7966b",
        "src/townlet/universe/validation/limits.py": "d2ae19642c66345db4ce02bf40f9ee08de90450029b03b952ee79bdcf442ad11",
        "src/townlet/universe/validation/references.py": "5e0f25757c226d3337c1133da071dc38ea6bbb585aa531eab782ffd5b02b5383",
        "src/townlet/universe/validation/semantics.py": "527b6ff869d16a42054860a3a321f3942a7e1b85c62a1a48a36c6e0aad5f0771",
        "src/townlet/universe/validation/static_access.py": "58bb7814eb3f3f2bfe1ef1c657b93160eb69dcd8037873f2f7d5f87a3cf88077",
        "src/townlet/vfs/__init__.py": "dd77714f6368dc803e31af8d50124b2bd5173117d14d19df14147af6e292cc27",
        "src/townlet/vfs/access_policy.py": "de4aede09b439f03d38262a06cb443d2d2ec6efd0d4312a090aa2a18a01f81f4",
        "src/townlet/vfs/communication.py": "7fd841663eead1c3bed1da2d492fee63d1a0037973d14dc45816dc9cd599dbf7",
        "src/townlet/vfs/dynamic_needs.py": "774a709d27eece64f9e0f47c610e357cffe52fd08a14b3d7136a1519e91406ea",
        "src/townlet/vfs/evaluator.py": "4bf6e3340ed3c1128912cbcf0ef6ffbd5a06d539579610e60c734b9d8762b75e",
        "src/townlet/vfs/generalisation.py": "65bc312df34adb4b7f17ec7e3994c7c74757dc0ea0a54857113f86d7c388c8f9",
        "src/townlet/vfs/history.py": "32905b5a1c297762742079907ea8805f088dc30b99f8401c612305c48939b74f",
        "src/townlet/vfs/profiles.py": "d6b560de4e480be43510bbdb7f9830a228fd75fa5b0f52030e0d749a6c602b83",
        "src/townlet/vfs/registry.py": "63ba294cf0a7c73fbe163e2684dafcb16cad2ba6a8b8cb39b6c885bc9ba1920e",
        "src/townlet/vfs/relational.py": "f721b9bb12095c81a9fa8df318230ec6970f680e9b5df2489fa5658a378d1f84",
        "src/townlet/vfs/schema.py": "4738d52b1a8ef7b763f661fa43b0be6167ae7c7fd9974cdb4123237bb9753a10",
        "src/townlet/vfs/schema_hashes.py": "da12619143fe9e426eafe907668243904c8b87b7610a78f30712186f9449f17c",
        "src/townlet/vfs/semantic_type.py": "ef0cc558b939c3b630f7618ee11699c1aa637e752736857d8d95b264f4dc098d",
        "src/townlet/vfs/transition_graph.py": "b272bf1432b220f76a8feff50401260789e69079beb8c6f865c87517dd258315",
        "src/townlet/vfs/transition_schedule.py": "9afc4f82e6b83ac64ed7b7068ef8a960a0c6fcac106782e458414bbf1d211297",
        "src/townlet/vfs/vtc.py": "37f85722e2795f1be545a6e37faa55e232fbe8042e1e8330827bb3126aab5bfd",
        "src/townlet/vfs/vtc_kernels.py": "f2dd6353ca901521cfa0a4983b114acdef0b2276dbdfb1f7ddc35840ec8d9e02",
        "src/townlet/world/__init__.py": "225dc9aad95dbe86147acc7c8deb09fdf3f041f4c2274c72e47d32d42e9155eb",
        "src/townlet/world/expression/__init__.py": "18c3a900bd974a71aed06ef67db1ddfefd54367b842384788c6a2bec649b9f55",
        "src/townlet/world/expression/ast_nodes.py": "fab4391a40641da33c02f5dbd1d49e103e8bdee7baf0366654c86244654038ad",
        "src/townlet/world/expression/context.py": "0d9dcda3d8919d1c8bcc83497918f2b707a072a22249476b74a69d8e7e0292a3",
        "src/townlet/world/expression/evaluator.py": "cc3862dc21c85cd912b96205eb8eeadaad6a39416c06c292b755b24ae14969bf",
        "src/townlet/world/expression/functions.py": "3c69313217eb963837d08bcca77c657f9f55659b1d71a788949dc1c10857b0fd",
        "src/townlet/world/expression/history.py": "1d5b6356acd91c19850b82a46960c3dedc624514230fd0f3fa5cb5c67a088b1b",
        "src/townlet/world/expression/parser.py": "b4deeab169267080ab672aebed6755301858475755d9545613b09239f783079a",
        "src/townlet/world/expression/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "src/townlet/world/expression/type_checker.py": "d70508adfa26cf2e550c3a0f802f8b7c4abaf86ab445e5d088f52d868ff6f978",
        "src/townlet/world/types/__init__.py": "6222af71011d945b5d218b63bd89c6c5af2672ec3541d95d2bdb38257a07b8d5",
        "src/townlet/world/types/primitive.py": "ab9beebe9b8e4befedbe5060560f8caefa8c37baf3cb3e2d9721ad91dffdfe12",
        "src/townlet/world/types/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    },
    "E2": {
      "sha": "10cfc83495146f49d8fd8aeb7f3ba149ab087f54",
      "source_root": "/home/john/hamlet/.worktrees/episode-lane-implementation/runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/sources/E2/src",
      "src_tree": "85adc434fb2c4cb6eeb8d788842de7e84692d3b8",
      "archive_sha256": "d18ba2bf6384bac6dd690397168b177e235790c2fdbed64738d6e915d43c60c5",
      "closure": {
        "src/townlet/__init__.py": "802316b1b3acf1050d09751438d90c55ea11466a35a233fbbd2c1574c89ff80b",
        "src/townlet/agent/__init__.py": "7c66a7875664264fa84f1ced05578f2aa667b2f972694807d30efc250cf0c13b",
        "src/townlet/agent/loss_factory.py": "34ae008c6df833118906421ade7421479272418999b265fd19382766800d3de5",
        "src/townlet/agent/network_factory.py": "976ff4f761c65981ce0f35812379abbdef940e81bed21e8f2715c2df02efb6fd",
        "src/townlet/agent/networks.py": "a318511db13002a0b222a1741b1c90af49d333ed129fbf15338193ce28cac7ca",
        "src/townlet/agent/optimizer_factory.py": "56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d",
        "src/townlet/agent/token_diagnostics.py": "5d6c4ed12a053167e5caf137be5537e4dc1de727216fe9bff36ac5a899c2cd0d",
        "src/townlet/agent/token_input.py": "2aaab1b6d524ec5371e1e3503c936c1359d2a241826315afdd088cfbb6d44ba3",
        "src/townlet/config/__init__.py": "f6a870d05e3f901d6ecfa39bbad890d14cf529172a250ce821005424e0ba4f9b",
        "src/townlet/config/actions_config.py": "bc4cfeead60fc22f7cd29204bda07e23a37b385fd15e86f28ac5e5df5c44350c",
        "src/townlet/config/affordance_masking.py": "d098f6c2ccc3110b8d71ba9896faf1eb2b2686eb24fc98d05412b20aa29a45e4",
        "src/townlet/config/affordances_v2_config.py": "57f3510259c016fdc0d063775752ab2afed4402ed72509e7403f0ff52a30c379",
        "src/townlet/config/bars_v2_config.py": "e675ee8693ab60641e5a71f738f8a68092549d6a5ff4e20605878eb2c2df91a2",
        "src/townlet/config/base.py": "77d39a08edd7045214b907b0ec156d9ef160669a57d57b9fa5537c9235571d39",
        "src/townlet/config/brain_config.py": "129e72918dc1753a25e204761ebff2978a0a28a2af226af0536b8ec2331834ee",
        "src/townlet/config/capability_config.py": "2761ad15f3bff36313a3d81a592f391faa0dfc8050315d58eb0b283c9162c579",
        "src/townlet/config/curriculum.py": "1ab88dced36a1277e0e161e55bd6d9e1d736c0b8e6be723fddfa8a30d97db393",
        "src/townlet/config/curriculum_config.py": "32f62734b99575a1d19f20f9d113e56e70960ec722e4a39a521c208edcf56a7c",
        "src/townlet/config/drive_as_code.py": "5b1a00313c39e695477d65703dd51b75e607b748d8b95d9cdd11d74c3a8b8b40",
        "src/townlet/config/effects_config.py": "f53679ccbf8ba85a27d3dfa92c15bf3944a1ded00d660793c77c5e1c01af1de3",
        "src/townlet/config/environment_config.py": "03de4c4007b1bcf3ce86a7a974d665cb887236a3f8e4d6fc808f6700ac8198ef",
        "src/townlet/config/experiment_config.py": "d4d7013fc8eeda910448aa4878cf3dc730f79f24b1d875629a1f62c1e4bb4ac6",
        "src/townlet/config/exploration.py": "50c9b69a287c414401ecff7fdf1af1661c18a5c0cbea822692429efdab251afb",
        "src/townlet/config/interaction_type.py": "dc08d3b6b8ef7e3ad0a94ef7c2a688d27cacd802c87fe9901edad6865d4a0b6d",
        "src/townlet/config/items_config.py": "2af1223f6f01f4a32d50a3f06aa91d32893e4783ee0cb62be439dccfefc8060b",
        "src/townlet/config/presentation_config.py": "9f44315a53bb1ae922335068c5f78fb1d8a646e9924124479b365b0cf4bbd08a",
        "src/townlet/config/stratum_config.py": "08473a0f3052f06ffb74ec85026a1deb91843206e9d22fb0487f109281f659a4",
        "src/townlet/config/training_v2_config.py": "996b508557aa1378642c7f455f5a5fb7a5961337d9a3fb9fc9582b3c800b07b4",
        "src/townlet/config/transition_rules_config.py": "8bfab492badfea9e24da5f4ae2cbe09629b031240036db99ab1ca16c1cf87751",
        "src/townlet/config/variables_config.py": "eb895c51d9b1983f7db539dbc949b33818fc1abf8de6190061dcfdbac565a4c9",
        "src/townlet/curriculum/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/curriculum/adversarial.py": "8ce48905b6163d25ff98f692af7986447245cc29eba47bcc248f10e4f4b8cf8b",
        "src/townlet/curriculum/base.py": "04bfb42f3b5d4faa3728be82d6c476448011fdb0c63788a24296839375b1ae26",
        "src/townlet/curriculum/factory.py": "82f464d5a3dfaaaca4e06cd1fffb7f2ddb5c2646ef62524214598d236846aabe",
        "src/townlet/curriculum/static.py": "4bce47073d50962defe1c405ca4a5fbda480e8321e2e38ff8e3558d7fafbf1be",
        "src/townlet/demo/__init__.py": "5237c34f4b094f949ae3d4983fc3edd057dd88329f64ca90d7c8d6ac3b150b0a",
        "src/townlet/demo/database.py": "945ea042fdacc9b265ce6a2e4b4d62fd9b876c816c6a00dd29df94d99d2bb082",
        "src/townlet/demo/live_inference.py": "5c8023d89312712587ad14c448659133a762ed62e2c38f423a2c474fa89c83f9",
        "src/townlet/demo/presentation.py": "81fd5a91b2a8bcc5dc0cae06c02892acd52fbde11a7dcfc95a11a62cf60b74d8",
        "src/townlet/demo/runner.py": "71c3c1b8b326a55ab78b4b19ee5f843e120919a41038043df608fd05b490add3",
        "src/townlet/demo/unified_server.py": "7ab22810e77496e3bfc310046adb69e00155119d035d914bdaaa3d070c9e4f37",
        "src/townlet/determinism.py": "73b8cd748bf1d495d0dfa22842e85c2e5a52421bd3081afbfd401eb0c0f14244",
        "src/townlet/effects/__init__.py": "94af62ccbac0dc840e3b2147ad7cdfd5d694961945ff478863cc12c3bec61b49",
        "src/townlet/effects/admission.py": "09407fc85cda41afea750f858dd2c0235af5d03064a4094d82b3bb1cee7bf3f9",
        "src/townlet/effects/affordance_identity.py": "bc073b35cb8a9bba55d5e42acca879838a9cad532673f98b40abea790fd1fb31",
        "src/townlet/effects/catalog.py": "d92e7e8d6a229643758156d35b1583a23bb327b93b5722b426bb2766b759ab48",
        "src/townlet/effects/collections.py": "686a5c6118177069a614bc9c451be830ad6ba92d548b56d2898cd6c30c0aaa81",
        "src/townlet/effects/compiler.py": "09d377f119427525153da3086c52064ec6fe9cf69fea429a5dddea61ada7064f",
        "src/townlet/effects/context.py": "ed23cbdf16734882dd5770f67fc2b34403378b332f5bdbf917559096947f3404",
        "src/townlet/effects/executor.py": "3cb5f6adc251469aaf7f6caddaa9b538a5a9d1807ea4e90cdf4efb0c2ee82d9a",
        "src/townlet/effects/manager.py": "dbfac81773c3b9876e3db1d036d71d510451a2476b446240f6649497f1203777",
        "src/townlet/effects/parser.py": "8219058196d705bf4b236bdae944a0e5fc6127d8040ba00c7b98bb53ae5a1bb0",
        "src/townlet/effects/scheduler.py": "4973ad2e614669f92b9334d720dcd9317c07569c8247c03b781f6c631e6d26c7",
        "src/townlet/effects/schema.py": "7d639c4824813c633935a770c0358a0ad53af6e8cfb336a96041376046f0bdcf",
        "src/townlet/environment/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/environment/action_builder.py": "2c1269579f0f17f88681be3811b2021bad4931c658a09767a035e37243ebf8bf",
        "src/townlet/environment/action_config.py": "42d966352145d8a6410349e429d3e1d8d687e78ab8f91372de6645520aeaf7d0",
        "src/townlet/environment/action_executor.py": "5c7b350a34ac78e193e63b977e73c3c246b46547d8cf6f3e46b501e765d969bd",
        "src/townlet/environment/action_labels.py": "c9b47042502e4491845125a0c14af6643f1e10174492ebdc33d2e043e5237b50",
        "src/townlet/environment/action_mask_builder.py": "02d57542a4fa340a1e69f819117c364366e7e1c947ebbf0d63b7663749293293",
        "src/townlet/environment/affordance_engine.py": "706a981bb78f3eb216e83b5e615180174dc7d2f2aa72e208b783c5fbe601fae3",
        "src/townlet/environment/affordance_layout.py": "af5474a54298246ab0d371382da7565c16c436802bc967233b2ac586272ac891",
        "src/townlet/environment/dac_engine.py": "c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6",
        "src/townlet/environment/env_factory.py": "ab9489d854fba3b644439b19a964190e78302a78132646132921c2ece7f0d232",
        "src/townlet/environment/null_managers.py": "670489567be0de077ab35f45b0536b964f521fcc263ef679491fc4a2348cb7d2",
        "src/townlet/environment/observation_encoder.py": "d7e31d1b35e81091efc8a87789864323f95779f97e4f1f3ba196a9cd76509054",
        "src/townlet/environment/reward_calculator.py": "6db3a8fb1fe8e3e29201bd89ca1b993995a35c797e3c3323bf17a07210a6b16b",
        "src/townlet/environment/substrate_action_validator.py": "c81ae44eddc072499c3f7d783149ca142012e671a4ea53f6f0efc8ec7908ec41",
        "src/townlet/environment/token_publishers.py": "0c9104f6f4da839ae616203f72cfd9e011923dc118c0ecf4fc8976c4ac31ac28",
        "src/townlet/environment/vectorized_env.py": "4c8fb105d26ebf5194a06bac26efabe10efbcda501da60155468e63b31e22447",
        "src/townlet/exploration/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/exploration/action_selection.py": "c5362a5078c7ecce9dfac0727364a346988054e83228975abaf0939369d48d3e",
        "src/townlet/exploration/adaptive_intrinsic.py": "80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9",
        "src/townlet/exploration/base.py": "49a9a23c2dcf3705a7712fc0bc74d11aa4b30aeee8fba1d0f87a609e05fbd1ae",
        "src/townlet/exploration/epsilon_greedy.py": "f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059",
        "src/townlet/exploration/rnd.py": "58200c260ab0535319b2747b0ff73368dbf50667a9c081de3de23c9df272059d",
        "src/townlet/items/__init__.py": "53401e4dcdcdf71a2f0d6bc1c98e24f3488b0a61da8b0ffb737b96465298550e",
        "src/townlet/items/action_handlers.py": "76c9a2d1a682d17be718a20e05ec432c9b5a3bf942ec0aca14035442d25c4359",
        "src/townlet/items/instance.py": "c9672879907eb1f9f1d94d7817683b51886b78712cfc819d0b9e976f5a2cbe51",
        "src/townlet/items/inventory.py": "175036c8faea2a53f34010276c5e4d7257e836c9420d15886d6b66e8dea31c35",
        "src/townlet/items/manager.py": "69a626220c46d69521e7997a24d453cdbd8fb08fd170ef81a504205792245fc6",
        "src/townlet/numeric.py": "96c53eac046b9268732e794c2375b99be6506f97f51a68465f8318d6bf52865d",
        "src/townlet/oracle/__init__.py": "aa1cb6cc0e190dfea45cea6f41df35f5cb7cef8292343d83e843610c41aa86b1",
        "src/townlet/oracle/driver.py": "f69ea42c0313b85bb5c4b5b9f668a4502e4988882485302438181edeb979bfab",
        "src/townlet/oracle/harness.py": "0896facbf37cfca897f11242feab2dc1c35041b1363603cf8947e76e7719f0d8",
        "src/townlet/oracle/matrix.py": "81bfe561f19cae191b832995d97cc20dd17d044cbc67fc37330f48ccdaced865",
        "src/townlet/oracle/trace_io.py": "bd7f1136ad29572152b1fee9084566e34982c4912f5c918cc14300fd35f3472c",
        "src/townlet/population/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/population/base.py": "b10f0e4ed767d91a487b9447a45bd82a2bf80a0696bf29fd4335a0728911b392",
        "src/townlet/population/runtime_registry.py": "1425748c6abbb01aff170be023547f5a5c11eb35c92d29ea416bbf848b461f50",
        "src/townlet/population/vectorized.py": "53ed3e6414fa45a5b677d318f97660195390bcb8f3c64b88b429ec23e16b2f1a",
        "src/townlet/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "src/townlet/recording/__init__.py": "141d8edde1c83f709f01f2c20878caef1ce2e77c9922280b13bff25fb2d24231",
        "src/townlet/recording/__main__.py": "b4ef951f6f24f434efb6d206eb617923fec08866f34f30aa54de1fd4d26aa7a2",
        "src/townlet/recording/criteria.py": "bcfb3eacf7ea72d1148958d4d3a3e56032dad2adbc7a0c2ce7a72b11e0185191",
        "src/townlet/recording/data_structures.py": "ac0ee45925a581c594add3757883070984d5b8842970cd5ef802903d37dc8940",
        "src/townlet/recording/recorder.py": "9d797ce3a295d0bb4cbb3f4a376cdc1d62d0965daf05704d09d088c53fdb90f0",
        "src/townlet/recording/replay.py": "44e6f79f9f2635420281d3160f2e792f78b10f9a807200600c3100af8837bef1",
        "src/townlet/recording/video_export.py": "057b129fe3a634260568998c57c3db58ccbdd870f544a9dff15add971614cf56",
        "src/townlet/recording/video_renderer.py": "650eedd5ac181a505d6bedc7628cf12245cbd5564cff19cf809106aba6246f88",
        "src/townlet/substrate/__init__.py": "a6f4a318bdfa4acd63a57c99159eff35091fb599542e0e1cc269df66f859d018",
        "src/townlet/substrate/aspatial.py": "bc4d3936b82946e32183e03a9fe9e0965883fa0fa70fea1382c77f471706b167",
        "src/townlet/substrate/base.py": "f9aee0e7fd64451778b025b7f747be86f4da46146bf8d83c94ae39ba39af4700",
        "src/townlet/substrate/continuous.py": "b310dd8df724fe41e01d9636261b665ee9e10474adc8d5418ed00a7c0d4bdac9",
        "src/townlet/substrate/continuousnd.py": "75b2bf30dcf2b2a35fcfc550bbefdcfb683282b7b791d55a15d3577b46d79312",
        "src/townlet/substrate/factory.py": "f1f58a457341a50e99ff8ea0d82f325b921a8c72a0fd2f0ba2e0b620ccadc918",
        "src/townlet/substrate/grid2d.py": "9f264b90cc15806210e26ba7f91d52be3e28f54d2dd570b775332497bd715d74",
        "src/townlet/substrate/grid3d.py": "c5416e5e5c4338f49ea521ea1a7a979f205f39bba757488990f7466ab7da859f",
        "src/townlet/substrate/gridnd.py": "c4fe656c20c53406d90c12f45069b6a4818ce40f0dd41989e7ae8dda5880fcae",
        "src/townlet/training/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/training/checkpoint_utils.py": "e1103a54385cf3aa06c291b168eb82396a7d19a5fe798d5511aa86e73cdd8efa",
        "src/townlet/training/prioritized_replay_buffer.py": "0248df10333845fd2498d10c2cfb9b59dabcce8c5e8f91f9e645bf9782f4c61c",
        "src/townlet/training/replay_buffer.py": "a1e6f7e43e71c233635a458bc6c01179f15ee0ce922bb02dfce4b4d7624f679c",
        "src/townlet/training/sequential_replay_buffer.py": "6c0b0d644677a6171f03e2ad62b8ab7b99669e401ac630bb2ea2106828e628a7",
        "src/townlet/training/state.py": "a9e88c8977081c1ad9abbc3d85d260f61139a5257894e1900770447bb9f061b0",
        "src/townlet/training/tensorboard_logger.py": "932c7bea6b6e705620a66e756dfa320d01496297f8a1b158c600eeed31474c4d",
        "src/townlet/universe/__init__.py": "f5f10ad3274dfc76983223297f2bc6c47bd7632d8a717e7f5a0f1bee2365c54d",
        "src/townlet/universe/__main__.py": "79026c2399e34a24b34270a69963f98961adbfb04a4cbb3466e66766579ed8d4",
        "src/townlet/universe/compiled.py": "b8ec290f8960bca25998927a42aa2f49c9c8f62ea239874a6e1dbde207aa95d9",
        "src/townlet/universe/compiler.py": "2b7bda405c5cddb7c571f8c0061afcc2a7f7e317b4c4a2609d84d267fb615c64",
        "src/townlet/universe/compilers/__init__.py": "22a0b17fa71b9bb29e4447227b80e9782107dcc95e557cc96e65fe67513c193e",
        "src/townlet/universe/compilers/actions.py": "68a7cf86d2d0e229bbe333ad223531343d3dee51ed72d9c021827754680c94ef",
        "src/townlet/universe/compilers/effects.py": "8f7f8d5b1532e559622ded012ce636cfb892d3ce60074a9fa90e1686d9a59b64",
        "src/townlet/universe/compilers/metadata.py": "02f80e102cd5c897d69fa202a32d7c5fcb92c516bed1d610401ecaf8029923d7",
        "src/townlet/universe/compilers/observation.py": "d5bcf686e15cef0e0ac17f9249872d87a84a0f9e3d2cb210709cf9d10e0a235e",
        "src/townlet/universe/compilers/optimization.py": "9cde440bf462cea96115f6131555c3426eda58036a88a23eb14827de95d0d406",
        "src/townlet/universe/compilers/vfs.py": "eb56da5e8b6e2f41c3f3cbce2ae73b4426433294d81e58ec373b2a75cdf6af6a",
        "src/townlet/universe/declarations.py": "be55efed027b2853a643b958c4a27ead1bd5d1092f26f4cbbdd3ffa6e4005f3f",
        "src/townlet/universe/dto/__init__.py": "e860d56790f1db0ba91ed0380d6c11ad0ca4ef993a6ecdcd76597d3dda7f124f",
        "src/townlet/universe/dto/action_metadata.py": "8c62dafbb4ffb275335c56366e4db22b911050cd446eea0ecfc3ea0a02dbca2c",
        "src/townlet/universe/dto/affordance_metadata.py": "8807059550a2fec1866739869468203c5c77a057eb723a094f31876d9e5f8629",
        "src/townlet/universe/dto/meter_metadata.py": "fbcd7146b0434ac23b91bc1a97492d8ed5c4de7fb9a88f21bcb748664b06a419",
        "src/townlet/universe/dto/token_spec.py": "44e867ea6cc6789a821618d1cd57eec1955bd52ff872922f15c7a98e3257f88a",
        "src/townlet/universe/dto/universe_metadata.py": "85f873e0fc11c784eed830f85f1808f76d7182f52980c89a0b43219073cc5ccd",
        "src/townlet/universe/error_codes.py": "ad49a82718fb7669bec8d4f5a8a43214398e7747173133d896f08c16d412b971",
        "src/townlet/universe/errors.py": "4f37e39c8eff21de3d202b08a099c12cf084a90bb7f8f6f04d7f103a517da02a",
        "src/townlet/universe/loaders/__init__.py": "12803c85f26b3183619cd987ba311f6cde3eab3b31e9899c955b6d9bd584b9a7",
        "src/townlet/universe/loaders/preflight.py": "7fc16741252e0bf6dd0a3fb68f9d492b8c18d1c03912a68fea748ef127bc3435",
        "src/townlet/universe/loaders/v21.py": "84a8543269af6cdbc9bbf79506a5ad79b9363f620501d387721e2eae62f56be2",
        "src/townlet/universe/optimization.py": "bba8c2c7fb2893096030f4a5e5ce89122e2d97a12535e10fdd6b96629be98aef",
        "src/townlet/universe/pipeline.py": "553db4b3d018d2f198fc0d2717ba53209ed5d65ab857c1eeb4358173f4f43768",
        "src/townlet/universe/raw_configs_v21.py": "7f370cb4370b59a3e6a590b9e94c75a7b0abc7cd3d3e9615fe39fa9c318834db",
        "src/townlet/universe/source_map.py": "70daa49af10108b45bf61df6fc471c2b75c3b22b816c8dfecf8057792812b3ec",
        "src/townlet/universe/stages.py": "7edd5fbfc98901b38e05b1eac0debb1dbec7e67dac17075495cdf5d4f77d84d9",
        "src/townlet/universe/symbol_table.py": "6342fef237fb321d8acf758da73434cd8a0da42e0ef5d5a055193819ef480e41",
        "src/townlet/universe/token_hashes.py": "996866109a60b84b9f3b0fc8e1cb0e3da622f13cf3be03f458654213b2cd24ae",
        "src/townlet/universe/validation/__init__.py": "c6c1f481cc1751e1f311c85ac96a735a3a18e0e4fdecaceebdbebd0c5d4be11b",
        "src/townlet/universe/validation/feasibility.py": "a8c1720c04a209c2256628792bdd7529dbede3fc9229ecdf1483ec9b17e7966b",
        "src/townlet/universe/validation/limits.py": "d2ae19642c66345db4ce02bf40f9ee08de90450029b03b952ee79bdcf442ad11",
        "src/townlet/universe/validation/references.py": "5e0f25757c226d3337c1133da071dc38ea6bbb585aa531eab782ffd5b02b5383",
        "src/townlet/universe/validation/semantics.py": "527b6ff869d16a42054860a3a321f3942a7e1b85c62a1a48a36c6e0aad5f0771",
        "src/townlet/universe/validation/static_access.py": "58bb7814eb3f3f2bfe1ef1c657b93160eb69dcd8037873f2f7d5f87a3cf88077",
        "src/townlet/vfs/__init__.py": "dd77714f6368dc803e31af8d50124b2bd5173117d14d19df14147af6e292cc27",
        "src/townlet/vfs/access_policy.py": "de4aede09b439f03d38262a06cb443d2d2ec6efd0d4312a090aa2a18a01f81f4",
        "src/townlet/vfs/communication.py": "7fd841663eead1c3bed1da2d492fee63d1a0037973d14dc45816dc9cd599dbf7",
        "src/townlet/vfs/dynamic_needs.py": "774a709d27eece64f9e0f47c610e357cffe52fd08a14b3d7136a1519e91406ea",
        "src/townlet/vfs/evaluator.py": "4bf6e3340ed3c1128912cbcf0ef6ffbd5a06d539579610e60c734b9d8762b75e",
        "src/townlet/vfs/generalisation.py": "65bc312df34adb4b7f17ec7e3994c7c74757dc0ea0a54857113f86d7c388c8f9",
        "src/townlet/vfs/history.py": "32905b5a1c297762742079907ea8805f088dc30b99f8401c612305c48939b74f",
        "src/townlet/vfs/profiles.py": "d6b560de4e480be43510bbdb7f9830a228fd75fa5b0f52030e0d749a6c602b83",
        "src/townlet/vfs/registry.py": "63ba294cf0a7c73fbe163e2684dafcb16cad2ba6a8b8cb39b6c885bc9ba1920e",
        "src/townlet/vfs/relational.py": "f721b9bb12095c81a9fa8df318230ec6970f680e9b5df2489fa5658a378d1f84",
        "src/townlet/vfs/schema.py": "4738d52b1a8ef7b763f661fa43b0be6167ae7c7fd9974cdb4123237bb9753a10",
        "src/townlet/vfs/schema_hashes.py": "da12619143fe9e426eafe907668243904c8b87b7610a78f30712186f9449f17c",
        "src/townlet/vfs/semantic_type.py": "ef0cc558b939c3b630f7618ee11699c1aa637e752736857d8d95b264f4dc098d",
        "src/townlet/vfs/transition_graph.py": "b272bf1432b220f76a8feff50401260789e69079beb8c6f865c87517dd258315",
        "src/townlet/vfs/transition_schedule.py": "9afc4f82e6b83ac64ed7b7068ef8a960a0c6fcac106782e458414bbf1d211297",
        "src/townlet/vfs/vtc.py": "37f85722e2795f1be545a6e37faa55e232fbe8042e1e8330827bb3126aab5bfd",
        "src/townlet/vfs/vtc_kernels.py": "f2dd6353ca901521cfa0a4983b114acdef0b2276dbdfb1f7ddc35840ec8d9e02",
        "src/townlet/world/__init__.py": "225dc9aad95dbe86147acc7c8deb09fdf3f041f4c2274c72e47d32d42e9155eb",
        "src/townlet/world/expression/__init__.py": "18c3a900bd974a71aed06ef67db1ddfefd54367b842384788c6a2bec649b9f55",
        "src/townlet/world/expression/ast_nodes.py": "fab4391a40641da33c02f5dbd1d49e103e8bdee7baf0366654c86244654038ad",
        "src/townlet/world/expression/context.py": "0d9dcda3d8919d1c8bcc83497918f2b707a072a22249476b74a69d8e7e0292a3",
        "src/townlet/world/expression/evaluator.py": "cc3862dc21c85cd912b96205eb8eeadaad6a39416c06c292b755b24ae14969bf",
        "src/townlet/world/expression/functions.py": "3c69313217eb963837d08bcca77c657f9f55659b1d71a788949dc1c10857b0fd",
        "src/townlet/world/expression/history.py": "1d5b6356acd91c19850b82a46960c3dedc624514230fd0f3fa5cb5c67a088b1b",
        "src/townlet/world/expression/parser.py": "b4deeab169267080ab672aebed6755301858475755d9545613b09239f783079a",
        "src/townlet/world/expression/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "src/townlet/world/expression/type_checker.py": "d70508adfa26cf2e550c3a0f802f8b7c4abaf86ab445e5d088f52d868ff6f978",
        "src/townlet/world/types/__init__.py": "6222af71011d945b5d218b63bd89c6c5af2672ec3541d95d2bdb38257a07b8d5",
        "src/townlet/world/types/primitive.py": "ab9beebe9b8e4befedbe5060560f8caefa8c37baf3cb3e2d9721ad91dffdfe12",
        "src/townlet/world/types/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      "direct_parent_sha": "bba09f10c69e724fd30d33a535af1d6a98d76b84",
      "direct_parent_src_tree": "7fefe5efb599515c919bdb9826ce1d6667fe5f8b"
    },
    "E3": {
      "sha": "904f166ad17f201619e60e6284fd1e41c492c77b",
      "source_root": "/home/john/hamlet/.worktrees/episode-lane-implementation/runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/sources/E3/src",
      "src_tree": "79f0a66dd3165f75184bffb90e3dc530d5ceb077",
      "archive_sha256": "65b1e0157af92dc388354dd4919f25f4058acbef74e5c0cc9a04ae1ea83eb079",
      "closure": {
        "src/townlet/__init__.py": "802316b1b3acf1050d09751438d90c55ea11466a35a233fbbd2c1574c89ff80b",
        "src/townlet/agent/__init__.py": "7c66a7875664264fa84f1ced05578f2aa667b2f972694807d30efc250cf0c13b",
        "src/townlet/agent/loss_factory.py": "34ae008c6df833118906421ade7421479272418999b265fd19382766800d3de5",
        "src/townlet/agent/network_factory.py": "976ff4f761c65981ce0f35812379abbdef940e81bed21e8f2715c2df02efb6fd",
        "src/townlet/agent/networks.py": "a318511db13002a0b222a1741b1c90af49d333ed129fbf15338193ce28cac7ca",
        "src/townlet/agent/optimizer_factory.py": "56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d",
        "src/townlet/agent/token_diagnostics.py": "5d6c4ed12a053167e5caf137be5537e4dc1de727216fe9bff36ac5a899c2cd0d",
        "src/townlet/agent/token_input.py": "2aaab1b6d524ec5371e1e3503c936c1359d2a241826315afdd088cfbb6d44ba3",
        "src/townlet/config/__init__.py": "f6a870d05e3f901d6ecfa39bbad890d14cf529172a250ce821005424e0ba4f9b",
        "src/townlet/config/actions_config.py": "bc4cfeead60fc22f7cd29204bda07e23a37b385fd15e86f28ac5e5df5c44350c",
        "src/townlet/config/affordance_masking.py": "d098f6c2ccc3110b8d71ba9896faf1eb2b2686eb24fc98d05412b20aa29a45e4",
        "src/townlet/config/affordances_v2_config.py": "57f3510259c016fdc0d063775752ab2afed4402ed72509e7403f0ff52a30c379",
        "src/townlet/config/bars_v2_config.py": "e675ee8693ab60641e5a71f738f8a68092549d6a5ff4e20605878eb2c2df91a2",
        "src/townlet/config/base.py": "77d39a08edd7045214b907b0ec156d9ef160669a57d57b9fa5537c9235571d39",
        "src/townlet/config/brain_config.py": "129e72918dc1753a25e204761ebff2978a0a28a2af226af0536b8ec2331834ee",
        "src/townlet/config/capability_config.py": "2761ad15f3bff36313a3d81a592f391faa0dfc8050315d58eb0b283c9162c579",
        "src/townlet/config/curriculum.py": "1ab88dced36a1277e0e161e55bd6d9e1d736c0b8e6be723fddfa8a30d97db393",
        "src/townlet/config/curriculum_config.py": "32f62734b99575a1d19f20f9d113e56e70960ec722e4a39a521c208edcf56a7c",
        "src/townlet/config/drive_as_code.py": "5b1a00313c39e695477d65703dd51b75e607b748d8b95d9cdd11d74c3a8b8b40",
        "src/townlet/config/effects_config.py": "f53679ccbf8ba85a27d3dfa92c15bf3944a1ded00d660793c77c5e1c01af1de3",
        "src/townlet/config/environment_config.py": "03de4c4007b1bcf3ce86a7a974d665cb887236a3f8e4d6fc808f6700ac8198ef",
        "src/townlet/config/experiment_config.py": "d4d7013fc8eeda910448aa4878cf3dc730f79f24b1d875629a1f62c1e4bb4ac6",
        "src/townlet/config/exploration.py": "50c9b69a287c414401ecff7fdf1af1661c18a5c0cbea822692429efdab251afb",
        "src/townlet/config/interaction_type.py": "dc08d3b6b8ef7e3ad0a94ef7c2a688d27cacd802c87fe9901edad6865d4a0b6d",
        "src/townlet/config/items_config.py": "2af1223f6f01f4a32d50a3f06aa91d32893e4783ee0cb62be439dccfefc8060b",
        "src/townlet/config/presentation_config.py": "9f44315a53bb1ae922335068c5f78fb1d8a646e9924124479b365b0cf4bbd08a",
        "src/townlet/config/stratum_config.py": "08473a0f3052f06ffb74ec85026a1deb91843206e9d22fb0487f109281f659a4",
        "src/townlet/config/training_v2_config.py": "996b508557aa1378642c7f455f5a5fb7a5961337d9a3fb9fc9582b3c800b07b4",
        "src/townlet/config/transition_rules_config.py": "8bfab492badfea9e24da5f4ae2cbe09629b031240036db99ab1ca16c1cf87751",
        "src/townlet/config/variables_config.py": "eb895c51d9b1983f7db539dbc949b33818fc1abf8de6190061dcfdbac565a4c9",
        "src/townlet/curriculum/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/curriculum/adversarial.py": "8ce48905b6163d25ff98f692af7986447245cc29eba47bcc248f10e4f4b8cf8b",
        "src/townlet/curriculum/base.py": "04bfb42f3b5d4faa3728be82d6c476448011fdb0c63788a24296839375b1ae26",
        "src/townlet/curriculum/factory.py": "82f464d5a3dfaaaca4e06cd1fffb7f2ddb5c2646ef62524214598d236846aabe",
        "src/townlet/curriculum/static.py": "4bce47073d50962defe1c405ca4a5fbda480e8321e2e38ff8e3558d7fafbf1be",
        "src/townlet/demo/__init__.py": "5237c34f4b094f949ae3d4983fc3edd057dd88329f64ca90d7c8d6ac3b150b0a",
        "src/townlet/demo/database.py": "945ea042fdacc9b265ce6a2e4b4d62fd9b876c816c6a00dd29df94d99d2bb082",
        "src/townlet/demo/live_inference.py": "5c8023d89312712587ad14c448659133a762ed62e2c38f423a2c474fa89c83f9",
        "src/townlet/demo/presentation.py": "81fd5a91b2a8bcc5dc0cae06c02892acd52fbde11a7dcfc95a11a62cf60b74d8",
        "src/townlet/demo/runner.py": "71c3c1b8b326a55ab78b4b19ee5f843e120919a41038043df608fd05b490add3",
        "src/townlet/demo/unified_server.py": "7ab22810e77496e3bfc310046adb69e00155119d035d914bdaaa3d070c9e4f37",
        "src/townlet/determinism.py": "73b8cd748bf1d495d0dfa22842e85c2e5a52421bd3081afbfd401eb0c0f14244",
        "src/townlet/effects/__init__.py": "94af62ccbac0dc840e3b2147ad7cdfd5d694961945ff478863cc12c3bec61b49",
        "src/townlet/effects/admission.py": "09407fc85cda41afea750f858dd2c0235af5d03064a4094d82b3bb1cee7bf3f9",
        "src/townlet/effects/affordance_identity.py": "bc073b35cb8a9bba55d5e42acca879838a9cad532673f98b40abea790fd1fb31",
        "src/townlet/effects/catalog.py": "d92e7e8d6a229643758156d35b1583a23bb327b93b5722b426bb2766b759ab48",
        "src/townlet/effects/collections.py": "686a5c6118177069a614bc9c451be830ad6ba92d548b56d2898cd6c30c0aaa81",
        "src/townlet/effects/compiler.py": "09d377f119427525153da3086c52064ec6fe9cf69fea429a5dddea61ada7064f",
        "src/townlet/effects/context.py": "ed23cbdf16734882dd5770f67fc2b34403378b332f5bdbf917559096947f3404",
        "src/townlet/effects/executor.py": "3cb5f6adc251469aaf7f6caddaa9b538a5a9d1807ea4e90cdf4efb0c2ee82d9a",
        "src/townlet/effects/manager.py": "dbfac81773c3b9876e3db1d036d71d510451a2476b446240f6649497f1203777",
        "src/townlet/effects/parser.py": "8219058196d705bf4b236bdae944a0e5fc6127d8040ba00c7b98bb53ae5a1bb0",
        "src/townlet/effects/scheduler.py": "4973ad2e614669f92b9334d720dcd9317c07569c8247c03b781f6c631e6d26c7",
        "src/townlet/effects/schema.py": "7d639c4824813c633935a770c0358a0ad53af6e8cfb336a96041376046f0bdcf",
        "src/townlet/environment/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/environment/action_builder.py": "2c1269579f0f17f88681be3811b2021bad4931c658a09767a035e37243ebf8bf",
        "src/townlet/environment/action_config.py": "42d966352145d8a6410349e429d3e1d8d687e78ab8f91372de6645520aeaf7d0",
        "src/townlet/environment/action_executor.py": "5c7b350a34ac78e193e63b977e73c3c246b46547d8cf6f3e46b501e765d969bd",
        "src/townlet/environment/action_labels.py": "c9b47042502e4491845125a0c14af6643f1e10174492ebdc33d2e043e5237b50",
        "src/townlet/environment/action_mask_builder.py": "02d57542a4fa340a1e69f819117c364366e7e1c947ebbf0d63b7663749293293",
        "src/townlet/environment/affordance_engine.py": "706a981bb78f3eb216e83b5e615180174dc7d2f2aa72e208b783c5fbe601fae3",
        "src/townlet/environment/affordance_layout.py": "af5474a54298246ab0d371382da7565c16c436802bc967233b2ac586272ac891",
        "src/townlet/environment/dac_engine.py": "c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6",
        "src/townlet/environment/env_factory.py": "ab9489d854fba3b644439b19a964190e78302a78132646132921c2ece7f0d232",
        "src/townlet/environment/null_managers.py": "670489567be0de077ab35f45b0536b964f521fcc263ef679491fc4a2348cb7d2",
        "src/townlet/environment/observation_encoder.py": "d7e31d1b35e81091efc8a87789864323f95779f97e4f1f3ba196a9cd76509054",
        "src/townlet/environment/reward_calculator.py": "095d5775428c072da4d62e36a216234804c4fddfedb0ab77da8fa9225525dea7",
        "src/townlet/environment/substrate_action_validator.py": "c81ae44eddc072499c3f7d783149ca142012e671a4ea53f6f0efc8ec7908ec41",
        "src/townlet/environment/token_publishers.py": "0c9104f6f4da839ae616203f72cfd9e011923dc118c0ecf4fc8976c4ac31ac28",
        "src/townlet/environment/vectorized_env.py": "5441e37847a2a2db051ad19437e5793fe5d577a84178937b74749b2f35696ae1",
        "src/townlet/exploration/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/exploration/action_selection.py": "c5362a5078c7ecce9dfac0727364a346988054e83228975abaf0939369d48d3e",
        "src/townlet/exploration/adaptive_intrinsic.py": "80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9",
        "src/townlet/exploration/base.py": "49a9a23c2dcf3705a7712fc0bc74d11aa4b30aeee8fba1d0f87a609e05fbd1ae",
        "src/townlet/exploration/epsilon_greedy.py": "f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059",
        "src/townlet/exploration/rnd.py": "58200c260ab0535319b2747b0ff73368dbf50667a9c081de3de23c9df272059d",
        "src/townlet/items/__init__.py": "53401e4dcdcdf71a2f0d6bc1c98e24f3488b0a61da8b0ffb737b96465298550e",
        "src/townlet/items/action_handlers.py": "76c9a2d1a682d17be718a20e05ec432c9b5a3bf942ec0aca14035442d25c4359",
        "src/townlet/items/instance.py": "c9672879907eb1f9f1d94d7817683b51886b78712cfc819d0b9e976f5a2cbe51",
        "src/townlet/items/inventory.py": "175036c8faea2a53f34010276c5e4d7257e836c9420d15886d6b66e8dea31c35",
        "src/townlet/items/manager.py": "69a626220c46d69521e7997a24d453cdbd8fb08fd170ef81a504205792245fc6",
        "src/townlet/numeric.py": "96c53eac046b9268732e794c2375b99be6506f97f51a68465f8318d6bf52865d",
        "src/townlet/oracle/__init__.py": "aa1cb6cc0e190dfea45cea6f41df35f5cb7cef8292343d83e843610c41aa86b1",
        "src/townlet/oracle/driver.py": "f69ea42c0313b85bb5c4b5b9f668a4502e4988882485302438181edeb979bfab",
        "src/townlet/oracle/harness.py": "0896facbf37cfca897f11242feab2dc1c35041b1363603cf8947e76e7719f0d8",
        "src/townlet/oracle/matrix.py": "81bfe561f19cae191b832995d97cc20dd17d044cbc67fc37330f48ccdaced865",
        "src/townlet/oracle/trace_io.py": "bd7f1136ad29572152b1fee9084566e34982c4912f5c918cc14300fd35f3472c",
        "src/townlet/population/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/population/base.py": "b10f0e4ed767d91a487b9447a45bd82a2bf80a0696bf29fd4335a0728911b392",
        "src/townlet/population/runtime_registry.py": "1425748c6abbb01aff170be023547f5a5c11eb35c92d29ea416bbf848b461f50",
        "src/townlet/population/vectorized.py": "53ed3e6414fa45a5b677d318f97660195390bcb8f3c64b88b429ec23e16b2f1a",
        "src/townlet/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "src/townlet/recording/__init__.py": "141d8edde1c83f709f01f2c20878caef1ce2e77c9922280b13bff25fb2d24231",
        "src/townlet/recording/__main__.py": "b4ef951f6f24f434efb6d206eb617923fec08866f34f30aa54de1fd4d26aa7a2",
        "src/townlet/recording/criteria.py": "bcfb3eacf7ea72d1148958d4d3a3e56032dad2adbc7a0c2ce7a72b11e0185191",
        "src/townlet/recording/data_structures.py": "ac0ee45925a581c594add3757883070984d5b8842970cd5ef802903d37dc8940",
        "src/townlet/recording/recorder.py": "9d797ce3a295d0bb4cbb3f4a376cdc1d62d0965daf05704d09d088c53fdb90f0",
        "src/townlet/recording/replay.py": "44e6f79f9f2635420281d3160f2e792f78b10f9a807200600c3100af8837bef1",
        "src/townlet/recording/video_export.py": "057b129fe3a634260568998c57c3db58ccbdd870f544a9dff15add971614cf56",
        "src/townlet/recording/video_renderer.py": "650eedd5ac181a505d6bedc7628cf12245cbd5564cff19cf809106aba6246f88",
        "src/townlet/substrate/__init__.py": "a6f4a318bdfa4acd63a57c99159eff35091fb599542e0e1cc269df66f859d018",
        "src/townlet/substrate/aspatial.py": "bc4d3936b82946e32183e03a9fe9e0965883fa0fa70fea1382c77f471706b167",
        "src/townlet/substrate/base.py": "f9aee0e7fd64451778b025b7f747be86f4da46146bf8d83c94ae39ba39af4700",
        "src/townlet/substrate/continuous.py": "b310dd8df724fe41e01d9636261b665ee9e10474adc8d5418ed00a7c0d4bdac9",
        "src/townlet/substrate/continuousnd.py": "75b2bf30dcf2b2a35fcfc550bbefdcfb683282b7b791d55a15d3577b46d79312",
        "src/townlet/substrate/factory.py": "f1f58a457341a50e99ff8ea0d82f325b921a8c72a0fd2f0ba2e0b620ccadc918",
        "src/townlet/substrate/grid2d.py": "9f264b90cc15806210e26ba7f91d52be3e28f54d2dd570b775332497bd715d74",
        "src/townlet/substrate/grid3d.py": "c5416e5e5c4338f49ea521ea1a7a979f205f39bba757488990f7466ab7da859f",
        "src/townlet/substrate/gridnd.py": "c4fe656c20c53406d90c12f45069b6a4818ce40f0dd41989e7ae8dda5880fcae",
        "src/townlet/training/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/training/checkpoint_utils.py": "e1103a54385cf3aa06c291b168eb82396a7d19a5fe798d5511aa86e73cdd8efa",
        "src/townlet/training/prioritized_replay_buffer.py": "0248df10333845fd2498d10c2cfb9b59dabcce8c5e8f91f9e645bf9782f4c61c",
        "src/townlet/training/replay_buffer.py": "a1e6f7e43e71c233635a458bc6c01179f15ee0ce922bb02dfce4b4d7624f679c",
        "src/townlet/training/sequential_replay_buffer.py": "6c0b0d644677a6171f03e2ad62b8ab7b99669e401ac630bb2ea2106828e628a7",
        "src/townlet/training/state.py": "a9e88c8977081c1ad9abbc3d85d260f61139a5257894e1900770447bb9f061b0",
        "src/townlet/training/tensorboard_logger.py": "932c7bea6b6e705620a66e756dfa320d01496297f8a1b158c600eeed31474c4d",
        "src/townlet/universe/__init__.py": "f5f10ad3274dfc76983223297f2bc6c47bd7632d8a717e7f5a0f1bee2365c54d",
        "src/townlet/universe/__main__.py": "79026c2399e34a24b34270a69963f98961adbfb04a4cbb3466e66766579ed8d4",
        "src/townlet/universe/compiled.py": "b8ec290f8960bca25998927a42aa2f49c9c8f62ea239874a6e1dbde207aa95d9",
        "src/townlet/universe/compiler.py": "2b7bda405c5cddb7c571f8c0061afcc2a7f7e317b4c4a2609d84d267fb615c64",
        "src/townlet/universe/compilers/__init__.py": "22a0b17fa71b9bb29e4447227b80e9782107dcc95e557cc96e65fe67513c193e",
        "src/townlet/universe/compilers/actions.py": "68a7cf86d2d0e229bbe333ad223531343d3dee51ed72d9c021827754680c94ef",
        "src/townlet/universe/compilers/effects.py": "8f7f8d5b1532e559622ded012ce636cfb892d3ce60074a9fa90e1686d9a59b64",
        "src/townlet/universe/compilers/metadata.py": "02f80e102cd5c897d69fa202a32d7c5fcb92c516bed1d610401ecaf8029923d7",
        "src/townlet/universe/compilers/observation.py": "d5bcf686e15cef0e0ac17f9249872d87a84a0f9e3d2cb210709cf9d10e0a235e",
        "src/townlet/universe/compilers/optimization.py": "9cde440bf462cea96115f6131555c3426eda58036a88a23eb14827de95d0d406",
        "src/townlet/universe/compilers/vfs.py": "eb56da5e8b6e2f41c3f3cbce2ae73b4426433294d81e58ec373b2a75cdf6af6a",
        "src/townlet/universe/declarations.py": "be55efed027b2853a643b958c4a27ead1bd5d1092f26f4cbbdd3ffa6e4005f3f",
        "src/townlet/universe/dto/__init__.py": "e860d56790f1db0ba91ed0380d6c11ad0ca4ef993a6ecdcd76597d3dda7f124f",
        "src/townlet/universe/dto/action_metadata.py": "8c62dafbb4ffb275335c56366e4db22b911050cd446eea0ecfc3ea0a02dbca2c",
        "src/townlet/universe/dto/affordance_metadata.py": "8807059550a2fec1866739869468203c5c77a057eb723a094f31876d9e5f8629",
        "src/townlet/universe/dto/meter_metadata.py": "fbcd7146b0434ac23b91bc1a97492d8ed5c4de7fb9a88f21bcb748664b06a419",
        "src/townlet/universe/dto/token_spec.py": "44e867ea6cc6789a821618d1cd57eec1955bd52ff872922f15c7a98e3257f88a",
        "src/townlet/universe/dto/universe_metadata.py": "85f873e0fc11c784eed830f85f1808f76d7182f52980c89a0b43219073cc5ccd",
        "src/townlet/universe/error_codes.py": "ad49a82718fb7669bec8d4f5a8a43214398e7747173133d896f08c16d412b971",
        "src/townlet/universe/errors.py": "4f37e39c8eff21de3d202b08a099c12cf084a90bb7f8f6f04d7f103a517da02a",
        "src/townlet/universe/loaders/__init__.py": "12803c85f26b3183619cd987ba311f6cde3eab3b31e9899c955b6d9bd584b9a7",
        "src/townlet/universe/loaders/preflight.py": "7fc16741252e0bf6dd0a3fb68f9d492b8c18d1c03912a68fea748ef127bc3435",
        "src/townlet/universe/loaders/v21.py": "84a8543269af6cdbc9bbf79506a5ad79b9363f620501d387721e2eae62f56be2",
        "src/townlet/universe/optimization.py": "bba8c2c7fb2893096030f4a5e5ce89122e2d97a12535e10fdd6b96629be98aef",
        "src/townlet/universe/pipeline.py": "553db4b3d018d2f198fc0d2717ba53209ed5d65ab857c1eeb4358173f4f43768",
        "src/townlet/universe/raw_configs_v21.py": "7f370cb4370b59a3e6a590b9e94c75a7b0abc7cd3d3e9615fe39fa9c318834db",
        "src/townlet/universe/source_map.py": "70daa49af10108b45bf61df6fc471c2b75c3b22b816c8dfecf8057792812b3ec",
        "src/townlet/universe/stages.py": "7edd5fbfc98901b38e05b1eac0debb1dbec7e67dac17075495cdf5d4f77d84d9",
        "src/townlet/universe/symbol_table.py": "6342fef237fb321d8acf758da73434cd8a0da42e0ef5d5a055193819ef480e41",
        "src/townlet/universe/token_hashes.py": "996866109a60b84b9f3b0fc8e1cb0e3da622f13cf3be03f458654213b2cd24ae",
        "src/townlet/universe/validation/__init__.py": "c6c1f481cc1751e1f311c85ac96a735a3a18e0e4fdecaceebdbebd0c5d4be11b",
        "src/townlet/universe/validation/feasibility.py": "a8c1720c04a209c2256628792bdd7529dbede3fc9229ecdf1483ec9b17e7966b",
        "src/townlet/universe/validation/limits.py": "d2ae19642c66345db4ce02bf40f9ee08de90450029b03b952ee79bdcf442ad11",
        "src/townlet/universe/validation/references.py": "5e0f25757c226d3337c1133da071dc38ea6bbb585aa531eab782ffd5b02b5383",
        "src/townlet/universe/validation/semantics.py": "527b6ff869d16a42054860a3a321f3942a7e1b85c62a1a48a36c6e0aad5f0771",
        "src/townlet/universe/validation/static_access.py": "58bb7814eb3f3f2bfe1ef1c657b93160eb69dcd8037873f2f7d5f87a3cf88077",
        "src/townlet/vfs/__init__.py": "dd77714f6368dc803e31af8d50124b2bd5173117d14d19df14147af6e292cc27",
        "src/townlet/vfs/access_policy.py": "de4aede09b439f03d38262a06cb443d2d2ec6efd0d4312a090aa2a18a01f81f4",
        "src/townlet/vfs/communication.py": "7fd841663eead1c3bed1da2d492fee63d1a0037973d14dc45816dc9cd599dbf7",
        "src/townlet/vfs/dynamic_needs.py": "774a709d27eece64f9e0f47c610e357cffe52fd08a14b3d7136a1519e91406ea",
        "src/townlet/vfs/evaluator.py": "4bf6e3340ed3c1128912cbcf0ef6ffbd5a06d539579610e60c734b9d8762b75e",
        "src/townlet/vfs/generalisation.py": "65bc312df34adb4b7f17ec7e3994c7c74757dc0ea0a54857113f86d7c388c8f9",
        "src/townlet/vfs/history.py": "32905b5a1c297762742079907ea8805f088dc30b99f8401c612305c48939b74f",
        "src/townlet/vfs/profiles.py": "d6b560de4e480be43510bbdb7f9830a228fd75fa5b0f52030e0d749a6c602b83",
        "src/townlet/vfs/registry.py": "63ba294cf0a7c73fbe163e2684dafcb16cad2ba6a8b8cb39b6c885bc9ba1920e",
        "src/townlet/vfs/relational.py": "f721b9bb12095c81a9fa8df318230ec6970f680e9b5df2489fa5658a378d1f84",
        "src/townlet/vfs/schema.py": "4738d52b1a8ef7b763f661fa43b0be6167ae7c7fd9974cdb4123237bb9753a10",
        "src/townlet/vfs/schema_hashes.py": "da12619143fe9e426eafe907668243904c8b87b7610a78f30712186f9449f17c",
        "src/townlet/vfs/semantic_type.py": "ef0cc558b939c3b630f7618ee11699c1aa637e752736857d8d95b264f4dc098d",
        "src/townlet/vfs/transition_graph.py": "b272bf1432b220f76a8feff50401260789e69079beb8c6f865c87517dd258315",
        "src/townlet/vfs/transition_schedule.py": "9afc4f82e6b83ac64ed7b7068ef8a960a0c6fcac106782e458414bbf1d211297",
        "src/townlet/vfs/vtc.py": "37f85722e2795f1be545a6e37faa55e232fbe8042e1e8330827bb3126aab5bfd",
        "src/townlet/vfs/vtc_kernels.py": "f2dd6353ca901521cfa0a4983b114acdef0b2276dbdfb1f7ddc35840ec8d9e02",
        "src/townlet/world/__init__.py": "225dc9aad95dbe86147acc7c8deb09fdf3f041f4c2274c72e47d32d42e9155eb",
        "src/townlet/world/expression/__init__.py": "18c3a900bd974a71aed06ef67db1ddfefd54367b842384788c6a2bec649b9f55",
        "src/townlet/world/expression/ast_nodes.py": "fab4391a40641da33c02f5dbd1d49e103e8bdee7baf0366654c86244654038ad",
        "src/townlet/world/expression/context.py": "0d9dcda3d8919d1c8bcc83497918f2b707a072a22249476b74a69d8e7e0292a3",
        "src/townlet/world/expression/evaluator.py": "cc3862dc21c85cd912b96205eb8eeadaad6a39416c06c292b755b24ae14969bf",
        "src/townlet/world/expression/functions.py": "3c69313217eb963837d08bcca77c657f9f55659b1d71a788949dc1c10857b0fd",
        "src/townlet/world/expression/history.py": "1d5b6356acd91c19850b82a46960c3dedc624514230fd0f3fa5cb5c67a088b1b",
        "src/townlet/world/expression/parser.py": "b4deeab169267080ab672aebed6755301858475755d9545613b09239f783079a",
        "src/townlet/world/expression/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "src/townlet/world/expression/type_checker.py": "d70508adfa26cf2e550c3a0f802f8b7c4abaf86ab445e5d088f52d868ff6f978",
        "src/townlet/world/types/__init__.py": "6222af71011d945b5d218b63bd89c6c5af2672ec3541d95d2bdb38257a07b8d5",
        "src/townlet/world/types/primitive.py": "ab9beebe9b8e4befedbe5060560f8caefa8c37baf3cb3e2d9721ad91dffdfe12",
        "src/townlet/world/types/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    },
    "candidate": {
      "sha": "8e3ca306d6f615bd272bb1c8d51b071b74686877",
      "source_root": "/home/john/hamlet/.worktrees/episode-lane-implementation/src",
      "src_tree": "f74f24beb81e1a172941ef817f0c62072e5b2be7",
      "closure": {
        "src/townlet/__init__.py": "802316b1b3acf1050d09751438d90c55ea11466a35a233fbbd2c1574c89ff80b",
        "src/townlet/agent/__init__.py": "7c66a7875664264fa84f1ced05578f2aa667b2f972694807d30efc250cf0c13b",
        "src/townlet/agent/loss_factory.py": "34ae008c6df833118906421ade7421479272418999b265fd19382766800d3de5",
        "src/townlet/agent/network_factory.py": "976ff4f761c65981ce0f35812379abbdef940e81bed21e8f2715c2df02efb6fd",
        "src/townlet/agent/networks.py": "a318511db13002a0b222a1741b1c90af49d333ed129fbf15338193ce28cac7ca",
        "src/townlet/agent/optimizer_factory.py": "56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d",
        "src/townlet/agent/token_diagnostics.py": "5d6c4ed12a053167e5caf137be5537e4dc1de727216fe9bff36ac5a899c2cd0d",
        "src/townlet/agent/token_input.py": "2aaab1b6d524ec5371e1e3503c936c1359d2a241826315afdd088cfbb6d44ba3",
        "src/townlet/config/__init__.py": "f6a870d05e3f901d6ecfa39bbad890d14cf529172a250ce821005424e0ba4f9b",
        "src/townlet/config/actions_config.py": "bc4cfeead60fc22f7cd29204bda07e23a37b385fd15e86f28ac5e5df5c44350c",
        "src/townlet/config/affordance_masking.py": "d098f6c2ccc3110b8d71ba9896faf1eb2b2686eb24fc98d05412b20aa29a45e4",
        "src/townlet/config/affordances_v2_config.py": "57f3510259c016fdc0d063775752ab2afed4402ed72509e7403f0ff52a30c379",
        "src/townlet/config/bars_v2_config.py": "e675ee8693ab60641e5a71f738f8a68092549d6a5ff4e20605878eb2c2df91a2",
        "src/townlet/config/base.py": "77d39a08edd7045214b907b0ec156d9ef160669a57d57b9fa5537c9235571d39",
        "src/townlet/config/brain_config.py": "129e72918dc1753a25e204761ebff2978a0a28a2af226af0536b8ec2331834ee",
        "src/townlet/config/capability_config.py": "2761ad15f3bff36313a3d81a592f391faa0dfc8050315d58eb0b283c9162c579",
        "src/townlet/config/curriculum.py": "1ab88dced36a1277e0e161e55bd6d9e1d736c0b8e6be723fddfa8a30d97db393",
        "src/townlet/config/curriculum_config.py": "32f62734b99575a1d19f20f9d113e56e70960ec722e4a39a521c208edcf56a7c",
        "src/townlet/config/drive_as_code.py": "5b1a00313c39e695477d65703dd51b75e607b748d8b95d9cdd11d74c3a8b8b40",
        "src/townlet/config/effects_config.py": "f53679ccbf8ba85a27d3dfa92c15bf3944a1ded00d660793c77c5e1c01af1de3",
        "src/townlet/config/environment_config.py": "03de4c4007b1bcf3ce86a7a974d665cb887236a3f8e4d6fc808f6700ac8198ef",
        "src/townlet/config/experiment_config.py": "d4d7013fc8eeda910448aa4878cf3dc730f79f24b1d875629a1f62c1e4bb4ac6",
        "src/townlet/config/exploration.py": "50c9b69a287c414401ecff7fdf1af1661c18a5c0cbea822692429efdab251afb",
        "src/townlet/config/interaction_type.py": "dc08d3b6b8ef7e3ad0a94ef7c2a688d27cacd802c87fe9901edad6865d4a0b6d",
        "src/townlet/config/items_config.py": "2af1223f6f01f4a32d50a3f06aa91d32893e4783ee0cb62be439dccfefc8060b",
        "src/townlet/config/presentation_config.py": "9f44315a53bb1ae922335068c5f78fb1d8a646e9924124479b365b0cf4bbd08a",
        "src/townlet/config/stratum_config.py": "08473a0f3052f06ffb74ec85026a1deb91843206e9d22fb0487f109281f659a4",
        "src/townlet/config/training_v2_config.py": "996b508557aa1378642c7f455f5a5fb7a5961337d9a3fb9fc9582b3c800b07b4",
        "src/townlet/config/transition_rules_config.py": "8bfab492badfea9e24da5f4ae2cbe09629b031240036db99ab1ca16c1cf87751",
        "src/townlet/config/variables_config.py": "eb895c51d9b1983f7db539dbc949b33818fc1abf8de6190061dcfdbac565a4c9",
        "src/townlet/curriculum/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/curriculum/adversarial.py": "8ce48905b6163d25ff98f692af7986447245cc29eba47bcc248f10e4f4b8cf8b",
        "src/townlet/curriculum/base.py": "04bfb42f3b5d4faa3728be82d6c476448011fdb0c63788a24296839375b1ae26",
        "src/townlet/curriculum/factory.py": "82f464d5a3dfaaaca4e06cd1fffb7f2ddb5c2646ef62524214598d236846aabe",
        "src/townlet/curriculum/static.py": "4bce47073d50962defe1c405ca4a5fbda480e8321e2e38ff8e3558d7fafbf1be",
        "src/townlet/demo/__init__.py": "5237c34f4b094f949ae3d4983fc3edd057dd88329f64ca90d7c8d6ac3b150b0a",
        "src/townlet/demo/database.py": "b11bc6ebf19bb684ea4d936d51cd0c261f8a3eae9cb768e983fde0b3b6251939",
        "src/townlet/demo/live_inference.py": "f003bc93ebea078a1698dba5b05561caef6595a2f89e2860c4cfba382f8ec16b",
        "src/townlet/demo/presentation.py": "81fd5a91b2a8bcc5dc0cae06c02892acd52fbde11a7dcfc95a11a62cf60b74d8",
        "src/townlet/demo/runner.py": "9666c863d1bad851cc51b97faafb4f13647d057e8ab78ae5b03b7aa37d811730",
        "src/townlet/demo/unified_server.py": "7ab22810e77496e3bfc310046adb69e00155119d035d914bdaaa3d070c9e4f37",
        "src/townlet/determinism.py": "73b8cd748bf1d495d0dfa22842e85c2e5a52421bd3081afbfd401eb0c0f14244",
        "src/townlet/effects/__init__.py": "94af62ccbac0dc840e3b2147ad7cdfd5d694961945ff478863cc12c3bec61b49",
        "src/townlet/effects/admission.py": "09407fc85cda41afea750f858dd2c0235af5d03064a4094d82b3bb1cee7bf3f9",
        "src/townlet/effects/affordance_identity.py": "bc073b35cb8a9bba55d5e42acca879838a9cad532673f98b40abea790fd1fb31",
        "src/townlet/effects/catalog.py": "d92e7e8d6a229643758156d35b1583a23bb327b93b5722b426bb2766b759ab48",
        "src/townlet/effects/collections.py": "686a5c6118177069a614bc9c451be830ad6ba92d548b56d2898cd6c30c0aaa81",
        "src/townlet/effects/compiler.py": "09d377f119427525153da3086c52064ec6fe9cf69fea429a5dddea61ada7064f",
        "src/townlet/effects/context.py": "ed23cbdf16734882dd5770f67fc2b34403378b332f5bdbf917559096947f3404",
        "src/townlet/effects/executor.py": "3cb5f6adc251469aaf7f6caddaa9b538a5a9d1807ea4e90cdf4efb0c2ee82d9a",
        "src/townlet/effects/manager.py": "dbfac81773c3b9876e3db1d036d71d510451a2476b446240f6649497f1203777",
        "src/townlet/effects/parser.py": "8219058196d705bf4b236bdae944a0e5fc6127d8040ba00c7b98bb53ae5a1bb0",
        "src/townlet/effects/scheduler.py": "4973ad2e614669f92b9334d720dcd9317c07569c8247c03b781f6c631e6d26c7",
        "src/townlet/effects/schema.py": "7d639c4824813c633935a770c0358a0ad53af6e8cfb336a96041376046f0bdcf",
        "src/townlet/environment/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/environment/action_builder.py": "2c1269579f0f17f88681be3811b2021bad4931c658a09767a035e37243ebf8bf",
        "src/townlet/environment/action_config.py": "42d966352145d8a6410349e429d3e1d8d687e78ab8f91372de6645520aeaf7d0",
        "src/townlet/environment/action_executor.py": "5c7b350a34ac78e193e63b977e73c3c246b46547d8cf6f3e46b501e765d969bd",
        "src/townlet/environment/action_labels.py": "c9b47042502e4491845125a0c14af6643f1e10174492ebdc33d2e043e5237b50",
        "src/townlet/environment/action_mask_builder.py": "02d57542a4fa340a1e69f819117c364366e7e1c947ebbf0d63b7663749293293",
        "src/townlet/environment/affordance_engine.py": "706a981bb78f3eb216e83b5e615180174dc7d2f2aa72e208b783c5fbe601fae3",
        "src/townlet/environment/affordance_layout.py": "af5474a54298246ab0d371382da7565c16c436802bc967233b2ac586272ac891",
        "src/townlet/environment/dac_engine.py": "c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6",
        "src/townlet/environment/env_factory.py": "ab9489d854fba3b644439b19a964190e78302a78132646132921c2ece7f0d232",
        "src/townlet/environment/null_managers.py": "670489567be0de077ab35f45b0536b964f521fcc263ef679491fc4a2348cb7d2",
        "src/townlet/environment/observation_encoder.py": "d7e31d1b35e81091efc8a87789864323f95779f97e4f1f3ba196a9cd76509054",
        "src/townlet/environment/reward_calculator.py": "095d5775428c072da4d62e36a216234804c4fddfedb0ab77da8fa9225525dea7",
        "src/townlet/environment/substrate_action_validator.py": "c81ae44eddc072499c3f7d783149ca142012e671a4ea53f6f0efc8ec7908ec41",
        "src/townlet/environment/token_publishers.py": "0c9104f6f4da839ae616203f72cfd9e011923dc118c0ecf4fc8976c4ac31ac28",
        "src/townlet/environment/vectorized_env.py": "5441e37847a2a2db051ad19437e5793fe5d577a84178937b74749b2f35696ae1",
        "src/townlet/exploration/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/exploration/action_selection.py": "c5362a5078c7ecce9dfac0727364a346988054e83228975abaf0939369d48d3e",
        "src/townlet/exploration/adaptive_intrinsic.py": "80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9",
        "src/townlet/exploration/base.py": "49a9a23c2dcf3705a7712fc0bc74d11aa4b30aeee8fba1d0f87a609e05fbd1ae",
        "src/townlet/exploration/epsilon_greedy.py": "f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059",
        "src/townlet/exploration/rnd.py": "58200c260ab0535319b2747b0ff73368dbf50667a9c081de3de23c9df272059d",
        "src/townlet/items/__init__.py": "53401e4dcdcdf71a2f0d6bc1c98e24f3488b0a61da8b0ffb737b96465298550e",
        "src/townlet/items/action_handlers.py": "76c9a2d1a682d17be718a20e05ec432c9b5a3bf942ec0aca14035442d25c4359",
        "src/townlet/items/instance.py": "c9672879907eb1f9f1d94d7817683b51886b78712cfc819d0b9e976f5a2cbe51",
        "src/townlet/items/inventory.py": "175036c8faea2a53f34010276c5e4d7257e836c9420d15886d6b66e8dea31c35",
        "src/townlet/items/manager.py": "69a626220c46d69521e7997a24d453cdbd8fb08fd170ef81a504205792245fc6",
        "src/townlet/numeric.py": "96c53eac046b9268732e794c2375b99be6506f97f51a68465f8318d6bf52865d",
        "src/townlet/oracle/__init__.py": "aa1cb6cc0e190dfea45cea6f41df35f5cb7cef8292343d83e843610c41aa86b1",
        "src/townlet/oracle/driver.py": "f69ea42c0313b85bb5c4b5b9f668a4502e4988882485302438181edeb979bfab",
        "src/townlet/oracle/harness.py": "0896facbf37cfca897f11242feab2dc1c35041b1363603cf8947e76e7719f0d8",
        "src/townlet/oracle/matrix.py": "81bfe561f19cae191b832995d97cc20dd17d044cbc67fc37330f48ccdaced865",
        "src/townlet/oracle/trace_io.py": "bd7f1136ad29572152b1fee9084566e34982c4912f5c918cc14300fd35f3472c",
        "src/townlet/population/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/population/base.py": "b10f0e4ed767d91a487b9447a45bd82a2bf80a0696bf29fd4335a0728911b392",
        "src/townlet/population/runtime_registry.py": "1425748c6abbb01aff170be023547f5a5c11eb35c92d29ea416bbf848b461f50",
        "src/townlet/population/vectorized.py": "eb4cae9eeee406566bef6a640212e382e2c61d551f2ff9d981c261f3d23da810",
        "src/townlet/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "src/townlet/recording/__init__.py": "141d8edde1c83f709f01f2c20878caef1ce2e77c9922280b13bff25fb2d24231",
        "src/townlet/recording/__main__.py": "b4ef951f6f24f434efb6d206eb617923fec08866f34f30aa54de1fd4d26aa7a2",
        "src/townlet/recording/criteria.py": "bcfb3eacf7ea72d1148958d4d3a3e56032dad2adbc7a0c2ce7a72b11e0185191",
        "src/townlet/recording/data_structures.py": "b8b2a5b2c202e8fc28ee907b645391cfb32f7d1a5530f528fa8ae6e076171158",
        "src/townlet/recording/recorder.py": "21ae3ab6f4ac197a516bc37e1d6dca63174e2f60ce1d4a0489ba36c68867c395",
        "src/townlet/recording/replay.py": "be3f15bfed74fb30ef88298f42393c98626f41133cd04d98939a3dd23acdc579",
        "src/townlet/recording/video_export.py": "64301e3a020dcb74ee83a19f00a581469ed042382eb8babd07ebe20c44f4b2b2",
        "src/townlet/recording/video_renderer.py": "650eedd5ac181a505d6bedc7628cf12245cbd5564cff19cf809106aba6246f88",
        "src/townlet/substrate/__init__.py": "a6f4a318bdfa4acd63a57c99159eff35091fb599542e0e1cc269df66f859d018",
        "src/townlet/substrate/aspatial.py": "bc4d3936b82946e32183e03a9fe9e0965883fa0fa70fea1382c77f471706b167",
        "src/townlet/substrate/base.py": "f9aee0e7fd64451778b025b7f747be86f4da46146bf8d83c94ae39ba39af4700",
        "src/townlet/substrate/continuous.py": "b310dd8df724fe41e01d9636261b665ee9e10474adc8d5418ed00a7c0d4bdac9",
        "src/townlet/substrate/continuousnd.py": "75b2bf30dcf2b2a35fcfc550bbefdcfb683282b7b791d55a15d3577b46d79312",
        "src/townlet/substrate/factory.py": "f1f58a457341a50e99ff8ea0d82f325b921a8c72a0fd2f0ba2e0b620ccadc918",
        "src/townlet/substrate/grid2d.py": "9f264b90cc15806210e26ba7f91d52be3e28f54d2dd570b775332497bd715d74",
        "src/townlet/substrate/grid3d.py": "c5416e5e5c4338f49ea521ea1a7a979f205f39bba757488990f7466ab7da859f",
        "src/townlet/substrate/gridnd.py": "c4fe656c20c53406d90c12f45069b6a4818ce40f0dd41989e7ae8dda5880fcae",
        "src/townlet/training/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
        "src/townlet/training/checkpoint_utils.py": "e1103a54385cf3aa06c291b168eb82396a7d19a5fe798d5511aa86e73cdd8efa",
        "src/townlet/training/episode.py": "d9f93e2b0551f04ac882ffc7e4a775d34352626af3e868679c00a962f52c00a7",
        "src/townlet/training/episode_accounting.py": "7a824b4589ede65110abf586686302cfe714cb72aedd20b4f5ae2e77d20cb0fd",
        "src/townlet/training/prioritized_replay_buffer.py": "0248df10333845fd2498d10c2cfb9b59dabcce8c5e8f91f9e645bf9782f4c61c",
        "src/townlet/training/replay_buffer.py": "a1e6f7e43e71c233635a458bc6c01179f15ee0ce922bb02dfce4b4d7624f679c",
        "src/townlet/training/sequential_replay_buffer.py": "6c0b0d644677a6171f03e2ad62b8ab7b99669e401ac630bb2ea2106828e628a7",
        "src/townlet/training/state.py": "a9e88c8977081c1ad9abbc3d85d260f61139a5257894e1900770447bb9f061b0",
        "src/townlet/training/tensorboard_logger.py": "36c5382d61c39598f98ece9402291f1e9ed2b90fd3b1440a51857da28ca7d791",
        "src/townlet/universe/__init__.py": "f5f10ad3274dfc76983223297f2bc6c47bd7632d8a717e7f5a0f1bee2365c54d",
        "src/townlet/universe/__main__.py": "79026c2399e34a24b34270a69963f98961adbfb04a4cbb3466e66766579ed8d4",
        "src/townlet/universe/compiled.py": "b8ec290f8960bca25998927a42aa2f49c9c8f62ea239874a6e1dbde207aa95d9",
        "src/townlet/universe/compiler.py": "2b7bda405c5cddb7c571f8c0061afcc2a7f7e317b4c4a2609d84d267fb615c64",
        "src/townlet/universe/compilers/__init__.py": "22a0b17fa71b9bb29e4447227b80e9782107dcc95e557cc96e65fe67513c193e",
        "src/townlet/universe/compilers/actions.py": "68a7cf86d2d0e229bbe333ad223531343d3dee51ed72d9c021827754680c94ef",
        "src/townlet/universe/compilers/effects.py": "8f7f8d5b1532e559622ded012ce636cfb892d3ce60074a9fa90e1686d9a59b64",
        "src/townlet/universe/compilers/metadata.py": "02f80e102cd5c897d69fa202a32d7c5fcb92c516bed1d610401ecaf8029923d7",
        "src/townlet/universe/compilers/observation.py": "d5bcf686e15cef0e0ac17f9249872d87a84a0f9e3d2cb210709cf9d10e0a235e",
        "src/townlet/universe/compilers/optimization.py": "9cde440bf462cea96115f6131555c3426eda58036a88a23eb14827de95d0d406",
        "src/townlet/universe/compilers/vfs.py": "eb56da5e8b6e2f41c3f3cbce2ae73b4426433294d81e58ec373b2a75cdf6af6a",
        "src/townlet/universe/declarations.py": "be55efed027b2853a643b958c4a27ead1bd5d1092f26f4cbbdd3ffa6e4005f3f",
        "src/townlet/universe/dto/__init__.py": "e860d56790f1db0ba91ed0380d6c11ad0ca4ef993a6ecdcd76597d3dda7f124f",
        "src/townlet/universe/dto/action_metadata.py": "8c62dafbb4ffb275335c56366e4db22b911050cd446eea0ecfc3ea0a02dbca2c",
        "src/townlet/universe/dto/affordance_metadata.py": "8807059550a2fec1866739869468203c5c77a057eb723a094f31876d9e5f8629",
        "src/townlet/universe/dto/meter_metadata.py": "fbcd7146b0434ac23b91bc1a97492d8ed5c4de7fb9a88f21bcb748664b06a419",
        "src/townlet/universe/dto/token_spec.py": "44e867ea6cc6789a821618d1cd57eec1955bd52ff872922f15c7a98e3257f88a",
        "src/townlet/universe/dto/universe_metadata.py": "85f873e0fc11c784eed830f85f1808f76d7182f52980c89a0b43219073cc5ccd",
        "src/townlet/universe/error_codes.py": "ad49a82718fb7669bec8d4f5a8a43214398e7747173133d896f08c16d412b971",
        "src/townlet/universe/errors.py": "4f37e39c8eff21de3d202b08a099c12cf084a90bb7f8f6f04d7f103a517da02a",
        "src/townlet/universe/loaders/__init__.py": "12803c85f26b3183619cd987ba311f6cde3eab3b31e9899c955b6d9bd584b9a7",
        "src/townlet/universe/loaders/preflight.py": "7fc16741252e0bf6dd0a3fb68f9d492b8c18d1c03912a68fea748ef127bc3435",
        "src/townlet/universe/loaders/v21.py": "84a8543269af6cdbc9bbf79506a5ad79b9363f620501d387721e2eae62f56be2",
        "src/townlet/universe/optimization.py": "bba8c2c7fb2893096030f4a5e5ce89122e2d97a12535e10fdd6b96629be98aef",
        "src/townlet/universe/pipeline.py": "553db4b3d018d2f198fc0d2717ba53209ed5d65ab857c1eeb4358173f4f43768",
        "src/townlet/universe/raw_configs_v21.py": "7f370cb4370b59a3e6a590b9e94c75a7b0abc7cd3d3e9615fe39fa9c318834db",
        "src/townlet/universe/source_map.py": "70daa49af10108b45bf61df6fc471c2b75c3b22b816c8dfecf8057792812b3ec",
        "src/townlet/universe/stages.py": "7edd5fbfc98901b38e05b1eac0debb1dbec7e67dac17075495cdf5d4f77d84d9",
        "src/townlet/universe/symbol_table.py": "6342fef237fb321d8acf758da73434cd8a0da42e0ef5d5a055193819ef480e41",
        "src/townlet/universe/token_hashes.py": "996866109a60b84b9f3b0fc8e1cb0e3da622f13cf3be03f458654213b2cd24ae",
        "src/townlet/universe/validation/__init__.py": "c6c1f481cc1751e1f311c85ac96a735a3a18e0e4fdecaceebdbebd0c5d4be11b",
        "src/townlet/universe/validation/feasibility.py": "a8c1720c04a209c2256628792bdd7529dbede3fc9229ecdf1483ec9b17e7966b",
        "src/townlet/universe/validation/limits.py": "d2ae19642c66345db4ce02bf40f9ee08de90450029b03b952ee79bdcf442ad11",
        "src/townlet/universe/validation/references.py": "5e0f25757c226d3337c1133da071dc38ea6bbb585aa531eab782ffd5b02b5383",
        "src/townlet/universe/validation/semantics.py": "527b6ff869d16a42054860a3a321f3942a7e1b85c62a1a48a36c6e0aad5f0771",
        "src/townlet/universe/validation/static_access.py": "58bb7814eb3f3f2bfe1ef1c657b93160eb69dcd8037873f2f7d5f87a3cf88077",
        "src/townlet/vfs/__init__.py": "dd77714f6368dc803e31af8d50124b2bd5173117d14d19df14147af6e292cc27",
        "src/townlet/vfs/access_policy.py": "de4aede09b439f03d38262a06cb443d2d2ec6efd0d4312a090aa2a18a01f81f4",
        "src/townlet/vfs/communication.py": "7fd841663eead1c3bed1da2d492fee63d1a0037973d14dc45816dc9cd599dbf7",
        "src/townlet/vfs/dynamic_needs.py": "774a709d27eece64f9e0f47c610e357cffe52fd08a14b3d7136a1519e91406ea",
        "src/townlet/vfs/evaluator.py": "4bf6e3340ed3c1128912cbcf0ef6ffbd5a06d539579610e60c734b9d8762b75e",
        "src/townlet/vfs/generalisation.py": "65bc312df34adb4b7f17ec7e3994c7c74757dc0ea0a54857113f86d7c388c8f9",
        "src/townlet/vfs/history.py": "32905b5a1c297762742079907ea8805f088dc30b99f8401c612305c48939b74f",
        "src/townlet/vfs/profiles.py": "d6b560de4e480be43510bbdb7f9830a228fd75fa5b0f52030e0d749a6c602b83",
        "src/townlet/vfs/registry.py": "63ba294cf0a7c73fbe163e2684dafcb16cad2ba6a8b8cb39b6c885bc9ba1920e",
        "src/townlet/vfs/relational.py": "f721b9bb12095c81a9fa8df318230ec6970f680e9b5df2489fa5658a378d1f84",
        "src/townlet/vfs/schema.py": "4738d52b1a8ef7b763f661fa43b0be6167ae7c7fd9974cdb4123237bb9753a10",
        "src/townlet/vfs/schema_hashes.py": "da12619143fe9e426eafe907668243904c8b87b7610a78f30712186f9449f17c",
        "src/townlet/vfs/semantic_type.py": "ef0cc558b939c3b630f7618ee11699c1aa637e752736857d8d95b264f4dc098d",
        "src/townlet/vfs/transition_graph.py": "b272bf1432b220f76a8feff50401260789e69079beb8c6f865c87517dd258315",
        "src/townlet/vfs/transition_schedule.py": "9afc4f82e6b83ac64ed7b7068ef8a960a0c6fcac106782e458414bbf1d211297",
        "src/townlet/vfs/vtc.py": "37f85722e2795f1be545a6e37faa55e232fbe8042e1e8330827bb3126aab5bfd",
        "src/townlet/vfs/vtc_kernels.py": "f2dd6353ca901521cfa0a4983b114acdef0b2276dbdfb1f7ddc35840ec8d9e02",
        "src/townlet/world/__init__.py": "225dc9aad95dbe86147acc7c8deb09fdf3f041f4c2274c72e47d32d42e9155eb",
        "src/townlet/world/expression/__init__.py": "18c3a900bd974a71aed06ef67db1ddfefd54367b842384788c6a2bec649b9f55",
        "src/townlet/world/expression/ast_nodes.py": "fab4391a40641da33c02f5dbd1d49e103e8bdee7baf0366654c86244654038ad",
        "src/townlet/world/expression/context.py": "0d9dcda3d8919d1c8bcc83497918f2b707a072a22249476b74a69d8e7e0292a3",
        "src/townlet/world/expression/evaluator.py": "cc3862dc21c85cd912b96205eb8eeadaad6a39416c06c292b755b24ae14969bf",
        "src/townlet/world/expression/functions.py": "3c69313217eb963837d08bcca77c657f9f55659b1d71a788949dc1c10857b0fd",
        "src/townlet/world/expression/history.py": "1d5b6356acd91c19850b82a46960c3dedc624514230fd0f3fa5cb5c67a088b1b",
        "src/townlet/world/expression/parser.py": "b4deeab169267080ab672aebed6755301858475755d9545613b09239f783079a",
        "src/townlet/world/expression/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "src/townlet/world/expression/type_checker.py": "d70508adfa26cf2e550c3a0f802f8b7c4abaf86ab445e5d088f52d868ff6f978",
        "src/townlet/world/types/__init__.py": "6222af71011d945b5d218b63bd89c6c5af2672ec3541d95d2bdb38257a07b8d5",
        "src/townlet/world/types/primitive.py": "ab9beebe9b8e4befedbe5060560f8caefa8c37baf3cb3e2d9721ad91dffdfe12",
        "src/townlet/world/types/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      "archive_sha256": "6c2f8277208022117c90a8b958296ec52ac5c0441648405a9bc4cc20ade6c563"
    }
  },
  "final_source_binding": {
    "sha": "462e8a3980845d76e7987cfea67fb63432bcb847",
    "source_root": "/home/john/hamlet/.worktrees/episode-lane-implementation/src",
    "src_tree": "325acd476544463f8c3e2b9dddd5c68310775a44",
    "archive_sha256": "9c797b35ad1fe0be4ca75511272330f34357a2e23a269e27bd150d78fa13c9cd",
    "closure": {
      "src/townlet/__init__.py": "802316b1b3acf1050d09751438d90c55ea11466a35a233fbbd2c1574c89ff80b",
      "src/townlet/agent/__init__.py": "7c66a7875664264fa84f1ced05578f2aa667b2f972694807d30efc250cf0c13b",
      "src/townlet/agent/loss_factory.py": "34ae008c6df833118906421ade7421479272418999b265fd19382766800d3de5",
      "src/townlet/agent/network_factory.py": "976ff4f761c65981ce0f35812379abbdef940e81bed21e8f2715c2df02efb6fd",
      "src/townlet/agent/networks.py": "a318511db13002a0b222a1741b1c90af49d333ed129fbf15338193ce28cac7ca",
      "src/townlet/agent/optimizer_factory.py": "56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d",
      "src/townlet/agent/token_diagnostics.py": "5d6c4ed12a053167e5caf137be5537e4dc1de727216fe9bff36ac5a899c2cd0d",
      "src/townlet/agent/token_input.py": "2aaab1b6d524ec5371e1e3503c936c1359d2a241826315afdd088cfbb6d44ba3",
      "src/townlet/config/__init__.py": "f6a870d05e3f901d6ecfa39bbad890d14cf529172a250ce821005424e0ba4f9b",
      "src/townlet/config/actions_config.py": "bc4cfeead60fc22f7cd29204bda07e23a37b385fd15e86f28ac5e5df5c44350c",
      "src/townlet/config/affordance_masking.py": "d098f6c2ccc3110b8d71ba9896faf1eb2b2686eb24fc98d05412b20aa29a45e4",
      "src/townlet/config/affordances_v2_config.py": "57f3510259c016fdc0d063775752ab2afed4402ed72509e7403f0ff52a30c379",
      "src/townlet/config/bars_v2_config.py": "e675ee8693ab60641e5a71f738f8a68092549d6a5ff4e20605878eb2c2df91a2",
      "src/townlet/config/base.py": "77d39a08edd7045214b907b0ec156d9ef160669a57d57b9fa5537c9235571d39",
      "src/townlet/config/brain_config.py": "129e72918dc1753a25e204761ebff2978a0a28a2af226af0536b8ec2331834ee",
      "src/townlet/config/capability_config.py": "2761ad15f3bff36313a3d81a592f391faa0dfc8050315d58eb0b283c9162c579",
      "src/townlet/config/curriculum.py": "1ab88dced36a1277e0e161e55bd6d9e1d736c0b8e6be723fddfa8a30d97db393",
      "src/townlet/config/curriculum_config.py": "32f62734b99575a1d19f20f9d113e56e70960ec722e4a39a521c208edcf56a7c",
      "src/townlet/config/drive_as_code.py": "5b1a00313c39e695477d65703dd51b75e607b748d8b95d9cdd11d74c3a8b8b40",
      "src/townlet/config/effects_config.py": "f53679ccbf8ba85a27d3dfa92c15bf3944a1ded00d660793c77c5e1c01af1de3",
      "src/townlet/config/environment_config.py": "03de4c4007b1bcf3ce86a7a974d665cb887236a3f8e4d6fc808f6700ac8198ef",
      "src/townlet/config/experiment_config.py": "d4d7013fc8eeda910448aa4878cf3dc730f79f24b1d875629a1f62c1e4bb4ac6",
      "src/townlet/config/exploration.py": "50c9b69a287c414401ecff7fdf1af1661c18a5c0cbea822692429efdab251afb",
      "src/townlet/config/interaction_type.py": "dc08d3b6b8ef7e3ad0a94ef7c2a688d27cacd802c87fe9901edad6865d4a0b6d",
      "src/townlet/config/items_config.py": "2af1223f6f01f4a32d50a3f06aa91d32893e4783ee0cb62be439dccfefc8060b",
      "src/townlet/config/presentation_config.py": "9f44315a53bb1ae922335068c5f78fb1d8a646e9924124479b365b0cf4bbd08a",
      "src/townlet/config/stratum_config.py": "08473a0f3052f06ffb74ec85026a1deb91843206e9d22fb0487f109281f659a4",
      "src/townlet/config/training_v2_config.py": "996b508557aa1378642c7f455f5a5fb7a5961337d9a3fb9fc9582b3c800b07b4",
      "src/townlet/config/transition_rules_config.py": "8bfab492badfea9e24da5f4ae2cbe09629b031240036db99ab1ca16c1cf87751",
      "src/townlet/config/variables_config.py": "eb895c51d9b1983f7db539dbc949b33818fc1abf8de6190061dcfdbac565a4c9",
      "src/townlet/curriculum/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
      "src/townlet/curriculum/adversarial.py": "8ce48905b6163d25ff98f692af7986447245cc29eba47bcc248f10e4f4b8cf8b",
      "src/townlet/curriculum/base.py": "04bfb42f3b5d4faa3728be82d6c476448011fdb0c63788a24296839375b1ae26",
      "src/townlet/curriculum/factory.py": "82f464d5a3dfaaaca4e06cd1fffb7f2ddb5c2646ef62524214598d236846aabe",
      "src/townlet/curriculum/static.py": "4bce47073d50962defe1c405ca4a5fbda480e8321e2e38ff8e3558d7fafbf1be",
      "src/townlet/demo/__init__.py": "5237c34f4b094f949ae3d4983fc3edd057dd88329f64ca90d7c8d6ac3b150b0a",
      "src/townlet/demo/database.py": "ad1df1dc5834e14b932f6f2ee91de514dc86e0a292939b4bf534ae498513446f",
      "src/townlet/demo/live_inference.py": "f003bc93ebea078a1698dba5b05561caef6595a2f89e2860c4cfba382f8ec16b",
      "src/townlet/demo/presentation.py": "81fd5a91b2a8bcc5dc0cae06c02892acd52fbde11a7dcfc95a11a62cf60b74d8",
      "src/townlet/demo/runner.py": "9666c863d1bad851cc51b97faafb4f13647d057e8ab78ae5b03b7aa37d811730",
      "src/townlet/demo/unified_server.py": "7ab22810e77496e3bfc310046adb69e00155119d035d914bdaaa3d070c9e4f37",
      "src/townlet/determinism.py": "73b8cd748bf1d495d0dfa22842e85c2e5a52421bd3081afbfd401eb0c0f14244",
      "src/townlet/effects/__init__.py": "94af62ccbac0dc840e3b2147ad7cdfd5d694961945ff478863cc12c3bec61b49",
      "src/townlet/effects/admission.py": "09407fc85cda41afea750f858dd2c0235af5d03064a4094d82b3bb1cee7bf3f9",
      "src/townlet/effects/affordance_identity.py": "bc073b35cb8a9bba55d5e42acca879838a9cad532673f98b40abea790fd1fb31",
      "src/townlet/effects/catalog.py": "d92e7e8d6a229643758156d35b1583a23bb327b93b5722b426bb2766b759ab48",
      "src/townlet/effects/collections.py": "686a5c6118177069a614bc9c451be830ad6ba92d548b56d2898cd6c30c0aaa81",
      "src/townlet/effects/compiler.py": "09d377f119427525153da3086c52064ec6fe9cf69fea429a5dddea61ada7064f",
      "src/townlet/effects/context.py": "ed23cbdf16734882dd5770f67fc2b34403378b332f5bdbf917559096947f3404",
      "src/townlet/effects/executor.py": "3cb5f6adc251469aaf7f6caddaa9b538a5a9d1807ea4e90cdf4efb0c2ee82d9a",
      "src/townlet/effects/manager.py": "dbfac81773c3b9876e3db1d036d71d510451a2476b446240f6649497f1203777",
      "src/townlet/effects/parser.py": "8219058196d705bf4b236bdae944a0e5fc6127d8040ba00c7b98bb53ae5a1bb0",
      "src/townlet/effects/scheduler.py": "4973ad2e614669f92b9334d720dcd9317c07569c8247c03b781f6c631e6d26c7",
      "src/townlet/effects/schema.py": "7d639c4824813c633935a770c0358a0ad53af6e8cfb336a96041376046f0bdcf",
      "src/townlet/environment/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
      "src/townlet/environment/action_builder.py": "2c1269579f0f17f88681be3811b2021bad4931c658a09767a035e37243ebf8bf",
      "src/townlet/environment/action_config.py": "42d966352145d8a6410349e429d3e1d8d687e78ab8f91372de6645520aeaf7d0",
      "src/townlet/environment/action_executor.py": "5c7b350a34ac78e193e63b977e73c3c246b46547d8cf6f3e46b501e765d969bd",
      "src/townlet/environment/action_labels.py": "c9b47042502e4491845125a0c14af6643f1e10174492ebdc33d2e043e5237b50",
      "src/townlet/environment/action_mask_builder.py": "02d57542a4fa340a1e69f819117c364366e7e1c947ebbf0d63b7663749293293",
      "src/townlet/environment/affordance_engine.py": "706a981bb78f3eb216e83b5e615180174dc7d2f2aa72e208b783c5fbe601fae3",
      "src/townlet/environment/affordance_layout.py": "af5474a54298246ab0d371382da7565c16c436802bc967233b2ac586272ac891",
      "src/townlet/environment/dac_engine.py": "c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6",
      "src/townlet/environment/env_factory.py": "ab9489d854fba3b644439b19a964190e78302a78132646132921c2ece7f0d232",
      "src/townlet/environment/null_managers.py": "670489567be0de077ab35f45b0536b964f521fcc263ef679491fc4a2348cb7d2",
      "src/townlet/environment/observation_encoder.py": "d7e31d1b35e81091efc8a87789864323f95779f97e4f1f3ba196a9cd76509054",
      "src/townlet/environment/reward_calculator.py": "095d5775428c072da4d62e36a216234804c4fddfedb0ab77da8fa9225525dea7",
      "src/townlet/environment/substrate_action_validator.py": "c81ae44eddc072499c3f7d783149ca142012e671a4ea53f6f0efc8ec7908ec41",
      "src/townlet/environment/token_publishers.py": "0c9104f6f4da839ae616203f72cfd9e011923dc118c0ecf4fc8976c4ac31ac28",
      "src/townlet/environment/vectorized_env.py": "5441e37847a2a2db051ad19437e5793fe5d577a84178937b74749b2f35696ae1",
      "src/townlet/exploration/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
      "src/townlet/exploration/action_selection.py": "c5362a5078c7ecce9dfac0727364a346988054e83228975abaf0939369d48d3e",
      "src/townlet/exploration/adaptive_intrinsic.py": "80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9",
      "src/townlet/exploration/base.py": "49a9a23c2dcf3705a7712fc0bc74d11aa4b30aeee8fba1d0f87a609e05fbd1ae",
      "src/townlet/exploration/epsilon_greedy.py": "f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059",
      "src/townlet/exploration/rnd.py": "58200c260ab0535319b2747b0ff73368dbf50667a9c081de3de23c9df272059d",
      "src/townlet/items/__init__.py": "53401e4dcdcdf71a2f0d6bc1c98e24f3488b0a61da8b0ffb737b96465298550e",
      "src/townlet/items/action_handlers.py": "76c9a2d1a682d17be718a20e05ec432c9b5a3bf942ec0aca14035442d25c4359",
      "src/townlet/items/instance.py": "c9672879907eb1f9f1d94d7817683b51886b78712cfc819d0b9e976f5a2cbe51",
      "src/townlet/items/inventory.py": "175036c8faea2a53f34010276c5e4d7257e836c9420d15886d6b66e8dea31c35",
      "src/townlet/items/manager.py": "69a626220c46d69521e7997a24d453cdbd8fb08fd170ef81a504205792245fc6",
      "src/townlet/numeric.py": "96c53eac046b9268732e794c2375b99be6506f97f51a68465f8318d6bf52865d",
      "src/townlet/oracle/__init__.py": "aa1cb6cc0e190dfea45cea6f41df35f5cb7cef8292343d83e843610c41aa86b1",
      "src/townlet/oracle/driver.py": "f69ea42c0313b85bb5c4b5b9f668a4502e4988882485302438181edeb979bfab",
      "src/townlet/oracle/harness.py": "0896facbf37cfca897f11242feab2dc1c35041b1363603cf8947e76e7719f0d8",
      "src/townlet/oracle/matrix.py": "81bfe561f19cae191b832995d97cc20dd17d044cbc67fc37330f48ccdaced865",
      "src/townlet/oracle/trace_io.py": "bd7f1136ad29572152b1fee9084566e34982c4912f5c918cc14300fd35f3472c",
      "src/townlet/population/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
      "src/townlet/population/base.py": "b10f0e4ed767d91a487b9447a45bd82a2bf80a0696bf29fd4335a0728911b392",
      "src/townlet/population/runtime_registry.py": "1425748c6abbb01aff170be023547f5a5c11eb35c92d29ea416bbf848b461f50",
      "src/townlet/population/vectorized.py": "eb4cae9eeee406566bef6a640212e382e2c61d551f2ff9d981c261f3d23da810",
      "src/townlet/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "src/townlet/recording/__init__.py": "141d8edde1c83f709f01f2c20878caef1ce2e77c9922280b13bff25fb2d24231",
      "src/townlet/recording/__main__.py": "b4ef951f6f24f434efb6d206eb617923fec08866f34f30aa54de1fd4d26aa7a2",
      "src/townlet/recording/criteria.py": "bcfb3eacf7ea72d1148958d4d3a3e56032dad2adbc7a0c2ce7a72b11e0185191",
      "src/townlet/recording/data_structures.py": "b8b2a5b2c202e8fc28ee907b645391cfb32f7d1a5530f528fa8ae6e076171158",
      "src/townlet/recording/recorder.py": "21ae3ab6f4ac197a516bc37e1d6dca63174e2f60ce1d4a0489ba36c68867c395",
      "src/townlet/recording/replay.py": "be3f15bfed74fb30ef88298f42393c98626f41133cd04d98939a3dd23acdc579",
      "src/townlet/recording/video_export.py": "64301e3a020dcb74ee83a19f00a581469ed042382eb8babd07ebe20c44f4b2b2",
      "src/townlet/recording/video_renderer.py": "650eedd5ac181a505d6bedc7628cf12245cbd5564cff19cf809106aba6246f88",
      "src/townlet/substrate/__init__.py": "a6f4a318bdfa4acd63a57c99159eff35091fb599542e0e1cc269df66f859d018",
      "src/townlet/substrate/aspatial.py": "bc4d3936b82946e32183e03a9fe9e0965883fa0fa70fea1382c77f471706b167",
      "src/townlet/substrate/base.py": "f9aee0e7fd64451778b025b7f747be86f4da46146bf8d83c94ae39ba39af4700",
      "src/townlet/substrate/continuous.py": "b310dd8df724fe41e01d9636261b665ee9e10474adc8d5418ed00a7c0d4bdac9",
      "src/townlet/substrate/continuousnd.py": "75b2bf30dcf2b2a35fcfc550bbefdcfb683282b7b791d55a15d3577b46d79312",
      "src/townlet/substrate/factory.py": "f1f58a457341a50e99ff8ea0d82f325b921a8c72a0fd2f0ba2e0b620ccadc918",
      "src/townlet/substrate/grid2d.py": "9f264b90cc15806210e26ba7f91d52be3e28f54d2dd570b775332497bd715d74",
      "src/townlet/substrate/grid3d.py": "c5416e5e5c4338f49ea521ea1a7a979f205f39bba757488990f7466ab7da859f",
      "src/townlet/substrate/gridnd.py": "c4fe656c20c53406d90c12f45069b6a4818ce40f0dd41989e7ae8dda5880fcae",
      "src/townlet/training/__init__.py": "2a3c875ed4cea9984b0c62983a18feb87970d3d658d7ab48e4c956d963b8830f",
      "src/townlet/training/checkpoint_utils.py": "e1103a54385cf3aa06c291b168eb82396a7d19a5fe798d5511aa86e73cdd8efa",
      "src/townlet/training/episode.py": "d9f93e2b0551f04ac882ffc7e4a775d34352626af3e868679c00a962f52c00a7",
      "src/townlet/training/episode_accounting.py": "62fd98aa2f1774404a3e158312030a2056c60172ca3b1d4046aa304d1cfb4d69",
      "src/townlet/training/prioritized_replay_buffer.py": "0248df10333845fd2498d10c2cfb9b59dabcce8c5e8f91f9e645bf9782f4c61c",
      "src/townlet/training/replay_buffer.py": "a1e6f7e43e71c233635a458bc6c01179f15ee0ce922bb02dfce4b4d7624f679c",
      "src/townlet/training/sequential_replay_buffer.py": "6c0b0d644677a6171f03e2ad62b8ab7b99669e401ac630bb2ea2106828e628a7",
      "src/townlet/training/state.py": "a9e88c8977081c1ad9abbc3d85d260f61139a5257894e1900770447bb9f061b0",
      "src/townlet/training/tensorboard_logger.py": "36c5382d61c39598f98ece9402291f1e9ed2b90fd3b1440a51857da28ca7d791",
      "src/townlet/universe/__init__.py": "f5f10ad3274dfc76983223297f2bc6c47bd7632d8a717e7f5a0f1bee2365c54d",
      "src/townlet/universe/__main__.py": "79026c2399e34a24b34270a69963f98961adbfb04a4cbb3466e66766579ed8d4",
      "src/townlet/universe/compiled.py": "b8ec290f8960bca25998927a42aa2f49c9c8f62ea239874a6e1dbde207aa95d9",
      "src/townlet/universe/compiler.py": "2b7bda405c5cddb7c571f8c0061afcc2a7f7e317b4c4a2609d84d267fb615c64",
      "src/townlet/universe/compilers/__init__.py": "22a0b17fa71b9bb29e4447227b80e9782107dcc95e557cc96e65fe67513c193e",
      "src/townlet/universe/compilers/actions.py": "68a7cf86d2d0e229bbe333ad223531343d3dee51ed72d9c021827754680c94ef",
      "src/townlet/universe/compilers/effects.py": "8f7f8d5b1532e559622ded012ce636cfb892d3ce60074a9fa90e1686d9a59b64",
      "src/townlet/universe/compilers/metadata.py": "02f80e102cd5c897d69fa202a32d7c5fcb92c516bed1d610401ecaf8029923d7",
      "src/townlet/universe/compilers/observation.py": "d5bcf686e15cef0e0ac17f9249872d87a84a0f9e3d2cb210709cf9d10e0a235e",
      "src/townlet/universe/compilers/optimization.py": "9cde440bf462cea96115f6131555c3426eda58036a88a23eb14827de95d0d406",
      "src/townlet/universe/compilers/vfs.py": "eb56da5e8b6e2f41c3f3cbce2ae73b4426433294d81e58ec373b2a75cdf6af6a",
      "src/townlet/universe/declarations.py": "be55efed027b2853a643b958c4a27ead1bd5d1092f26f4cbbdd3ffa6e4005f3f",
      "src/townlet/universe/dto/__init__.py": "e860d56790f1db0ba91ed0380d6c11ad0ca4ef993a6ecdcd76597d3dda7f124f",
      "src/townlet/universe/dto/action_metadata.py": "8c62dafbb4ffb275335c56366e4db22b911050cd446eea0ecfc3ea0a02dbca2c",
      "src/townlet/universe/dto/affordance_metadata.py": "8807059550a2fec1866739869468203c5c77a057eb723a094f31876d9e5f8629",
      "src/townlet/universe/dto/meter_metadata.py": "fbcd7146b0434ac23b91bc1a97492d8ed5c4de7fb9a88f21bcb748664b06a419",
      "src/townlet/universe/dto/token_spec.py": "44e867ea6cc6789a821618d1cd57eec1955bd52ff872922f15c7a98e3257f88a",
      "src/townlet/universe/dto/universe_metadata.py": "85f873e0fc11c784eed830f85f1808f76d7182f52980c89a0b43219073cc5ccd",
      "src/townlet/universe/error_codes.py": "ad49a82718fb7669bec8d4f5a8a43214398e7747173133d896f08c16d412b971",
      "src/townlet/universe/errors.py": "4f37e39c8eff21de3d202b08a099c12cf084a90bb7f8f6f04d7f103a517da02a",
      "src/townlet/universe/loaders/__init__.py": "12803c85f26b3183619cd987ba311f6cde3eab3b31e9899c955b6d9bd584b9a7",
      "src/townlet/universe/loaders/preflight.py": "7fc16741252e0bf6dd0a3fb68f9d492b8c18d1c03912a68fea748ef127bc3435",
      "src/townlet/universe/loaders/v21.py": "84a8543269af6cdbc9bbf79506a5ad79b9363f620501d387721e2eae62f56be2",
      "src/townlet/universe/optimization.py": "bba8c2c7fb2893096030f4a5e5ce89122e2d97a12535e10fdd6b96629be98aef",
      "src/townlet/universe/pipeline.py": "553db4b3d018d2f198fc0d2717ba53209ed5d65ab857c1eeb4358173f4f43768",
      "src/townlet/universe/raw_configs_v21.py": "7f370cb4370b59a3e6a590b9e94c75a7b0abc7cd3d3e9615fe39fa9c318834db",
      "src/townlet/universe/source_map.py": "70daa49af10108b45bf61df6fc471c2b75c3b22b816c8dfecf8057792812b3ec",
      "src/townlet/universe/stages.py": "7edd5fbfc98901b38e05b1eac0debb1dbec7e67dac17075495cdf5d4f77d84d9",
      "src/townlet/universe/symbol_table.py": "6342fef237fb321d8acf758da73434cd8a0da42e0ef5d5a055193819ef480e41",
      "src/townlet/universe/token_hashes.py": "996866109a60b84b9f3b0fc8e1cb0e3da622f13cf3be03f458654213b2cd24ae",
      "src/townlet/universe/validation/__init__.py": "c6c1f481cc1751e1f311c85ac96a735a3a18e0e4fdecaceebdbebd0c5d4be11b",
      "src/townlet/universe/validation/feasibility.py": "a8c1720c04a209c2256628792bdd7529dbede3fc9229ecdf1483ec9b17e7966b",
      "src/townlet/universe/validation/limits.py": "d2ae19642c66345db4ce02bf40f9ee08de90450029b03b952ee79bdcf442ad11",
      "src/townlet/universe/validation/references.py": "5e0f25757c226d3337c1133da071dc38ea6bbb585aa531eab782ffd5b02b5383",
      "src/townlet/universe/validation/semantics.py": "527b6ff869d16a42054860a3a321f3942a7e1b85c62a1a48a36c6e0aad5f0771",
      "src/townlet/universe/validation/static_access.py": "58bb7814eb3f3f2bfe1ef1c657b93160eb69dcd8037873f2f7d5f87a3cf88077",
      "src/townlet/vfs/__init__.py": "dd77714f6368dc803e31af8d50124b2bd5173117d14d19df14147af6e292cc27",
      "src/townlet/vfs/access_policy.py": "de4aede09b439f03d38262a06cb443d2d2ec6efd0d4312a090aa2a18a01f81f4",
      "src/townlet/vfs/communication.py": "7fd841663eead1c3bed1da2d492fee63d1a0037973d14dc45816dc9cd599dbf7",
      "src/townlet/vfs/dynamic_needs.py": "774a709d27eece64f9e0f47c610e357cffe52fd08a14b3d7136a1519e91406ea",
      "src/townlet/vfs/evaluator.py": "4bf6e3340ed3c1128912cbcf0ef6ffbd5a06d539579610e60c734b9d8762b75e",
      "src/townlet/vfs/generalisation.py": "65bc312df34adb4b7f17ec7e3994c7c74757dc0ea0a54857113f86d7c388c8f9",
      "src/townlet/vfs/history.py": "32905b5a1c297762742079907ea8805f088dc30b99f8401c612305c48939b74f",
      "src/townlet/vfs/profiles.py": "d6b560de4e480be43510bbdb7f9830a228fd75fa5b0f52030e0d749a6c602b83",
      "src/townlet/vfs/registry.py": "63ba294cf0a7c73fbe163e2684dafcb16cad2ba6a8b8cb39b6c885bc9ba1920e",
      "src/townlet/vfs/relational.py": "f721b9bb12095c81a9fa8df318230ec6970f680e9b5df2489fa5658a378d1f84",
      "src/townlet/vfs/schema.py": "4738d52b1a8ef7b763f661fa43b0be6167ae7c7fd9974cdb4123237bb9753a10",
      "src/townlet/vfs/schema_hashes.py": "da12619143fe9e426eafe907668243904c8b87b7610a78f30712186f9449f17c",
      "src/townlet/vfs/semantic_type.py": "ef0cc558b939c3b630f7618ee11699c1aa637e752736857d8d95b264f4dc098d",
      "src/townlet/vfs/transition_graph.py": "b272bf1432b220f76a8feff50401260789e69079beb8c6f865c87517dd258315",
      "src/townlet/vfs/transition_schedule.py": "9afc4f82e6b83ac64ed7b7068ef8a960a0c6fcac106782e458414bbf1d211297",
      "src/townlet/vfs/vtc.py": "37f85722e2795f1be545a6e37faa55e232fbe8042e1e8330827bb3126aab5bfd",
      "src/townlet/vfs/vtc_kernels.py": "f2dd6353ca901521cfa0a4983b114acdef0b2276dbdfb1f7ddc35840ec8d9e02",
      "src/townlet/world/__init__.py": "225dc9aad95dbe86147acc7c8deb09fdf3f041f4c2274c72e47d32d42e9155eb",
      "src/townlet/world/expression/__init__.py": "18c3a900bd974a71aed06ef67db1ddfefd54367b842384788c6a2bec649b9f55",
      "src/townlet/world/expression/ast_nodes.py": "fab4391a40641da33c02f5dbd1d49e103e8bdee7baf0366654c86244654038ad",
      "src/townlet/world/expression/context.py": "0d9dcda3d8919d1c8bcc83497918f2b707a072a22249476b74a69d8e7e0292a3",
      "src/townlet/world/expression/evaluator.py": "cc3862dc21c85cd912b96205eb8eeadaad6a39416c06c292b755b24ae14969bf",
      "src/townlet/world/expression/functions.py": "3c69313217eb963837d08bcca77c657f9f55659b1d71a788949dc1c10857b0fd",
      "src/townlet/world/expression/history.py": "1d5b6356acd91c19850b82a46960c3dedc624514230fd0f3fa5cb5c67a088b1b",
      "src/townlet/world/expression/parser.py": "b4deeab169267080ab672aebed6755301858475755d9545613b09239f783079a",
      "src/townlet/world/expression/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "src/townlet/world/expression/type_checker.py": "d70508adfa26cf2e550c3a0f802f8b7c4abaf86ab445e5d088f52d868ff6f978",
      "src/townlet/world/types/__init__.py": "6222af71011d945b5d218b63bd89c6c5af2672ec3541d95d2bdb38257a07b8d5",
      "src/townlet/world/types/primitive.py": "ab9beebe9b8e4befedbe5060560f8caefa8c37baf3cb3e2d9721ad91dffdfe12",
      "src/townlet/world/types/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  },
  "final_source_differences": {
    "src/townlet/demo/database.py": {
      "retained": "b11bc6ebf19bb684ea4d936d51cd0c261f8a3eae9cb768e983fde0b3b6251939",
      "final": "ad1df1dc5834e14b932f6f2ee91de514dc86e0a292939b4bf534ae498513446f"
    },
    "src/townlet/training/episode_accounting.py": {
      "retained": "7a824b4589ede65110abf586686302cfe714cb72aedd20b4f5ae2e77d20cb0fd",
      "final": "62fd98aa2f1774404a3e158312030a2056c60172ca3b1d4046aa304d1cfb4d69"
    }
  },
  "verification_roots": {
    "parent": "/home/john/hamlet/.worktrees/episode-lane-implementation/runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/sources/parent/src",
    "E2": "/home/john/hamlet/.worktrees/episode-lane-implementation/runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/sources/E2/src",
    "E3": "/home/john/hamlet/.worktrees/episode-lane-implementation/runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/sources/E3/src",
    "candidate": "/home/john/hamlet/.worktrees/episode-lane-implementation/runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/sources/candidate/src",
    "final-candidate": "/home/john/hamlet/.worktrees/episode-lane-implementation/src"
  },
  "exact_changed_coordinates": {
    "cpu-08": [
      [
        99,
        0
      ],
      [
        99,
        1
      ],
      [
        99,
        3
      ]
    ],
    "cpu-09": [
      [
        99,
        0
      ],
      [
        99,
        1
      ],
      [
        99,
        2
      ],
      [
        99,
        3
      ]
    ]
  },
  "actual_counts": {
    "cpu-08": [
      49,
      51,
      100,
      54
    ],
    "cpu-09": [
      65,
      67,
      62,
      60
    ]
  },
  "lifespan": 100,
  "exact_old_bits": "0x3f800000",
  "exact_new_bits": "0x00000000",
  "negative_controls": [
    "live_reward_one_float32_ulp",
    "retained_false_bonus",
    "dropped_expected_difference",
    "swapped_lane_coordinates",
    "undesigned_dead_reward",
    "undesigned_signed_zero",
    "wrong_designated_magnitude",
    "wrong_designated_signed_zero",
    "changed_observation",
    "changed_action",
    "changed_done",
    "changed_hash",
    "nonfinite_reward",
    "nonfinite_observation",
    "changed_reward_dtype",
    "changed_reward_shape",
    "forged_active_entry",
    "forged_new_terminal",
    "forged_new_retirement",
    "advanced_completed_counter",
    "wrong_independent_survival",
    "changed_world_tick",
    "changed_lifespan",
    "changed_raw_DAC",
    "changed_E2_component",
    "changed_E3_component",
    "genuine_retirement_reward_corruption",
    "stale_allowance",
    "unused_expected_coordinate",
    "swapped_allowance_coordinates",
    "omitted_static_trace",
    "omitted_inventory",
    "changed_identity_reading",
    "omitted_reset",
    "changed_reset",
    "changed_registered_verdict",
    "omitted_cuda_skip",
    "changed_skip_reason",
    "changed_source_binding",
    "changed_config_binding",
    "changed_import_root",
    "changed_original_dirty_flag"
  ],
  "recipes": {
    "census": [
      {
        "pack": "configs/L5_multi_agent",
        "primary_level": "L5_multi_agent"
      },
      {
        "pack": "configs/aspatial_test",
        "primary_level": "L0"
      },
      {
        "pack": "configs/default_curriculum",
        "primary_level": "L0_0_minimal"
      },
      {
        "pack": "configs/default_curriculum",
        "primary_level": "L0_5_dual_resource"
      },
      {
        "pack": "configs/default_curriculum",
        "primary_level": "L1_full_observability"
      },
      {
        "pack": "configs/default_curriculum",
        "primary_level": "L2_partial_observability"
      },
      {
        "pack": "configs/default_curriculum",
        "primary_level": "L3_temporal_mechanics"
      },
      {
        "pack": "configs/differential/boundary_wrap",
        "primary_level": "L1_full_observability"
      },
      {
        "pack": "configs/differential/div003_cubic_partial",
        "primary_level": "L2_partial_observability"
      },
      {
        "pack": "configs/differential/div003_rect",
        "primary_level": "L1_full_observability"
      },
      {
        "pack": "configs/reference/model_pack",
        "primary_level": "L0_demo"
      },
      {
        "pack": "configs/simple",
        "primary_level": "L0_simple"
      },
      {
        "pack": "configs/test/action_masking",
        "primary_level": "L0_masking"
      },
      {
        "pack": "configs/test/action_space/aspatial",
        "primary_level": "L0"
      },
      {
        "pack": "configs/test/action_space/continuous1d",
        "primary_level": "L0"
      },
      {
        "pack": "configs/test/action_space/grid2d",
        "primary_level": "L0"
      },
      {
        "pack": "configs/test/effects_smoke",
        "primary_level": "L0_effects"
      },
      {
        "pack": "configs/test/gridnd_4d_pack",
        "primary_level": "L0_test"
      },
      {
        "pack": "configs/test/items_smoke",
        "primary_level": "L0_smoke"
      },
      {
        "pack": "configs/test/model_config",
        "primary_level": "L0_test"
      },
      {
        "pack": "configs/test/model_config_12meter",
        "primary_level": "L0_12meter"
      },
      {
        "pack": "configs/test/model_config_4meter",
        "primary_level": "L0_4meter"
      },
      {
        "pack": "configs/test/token_set_smoke",
        "primary_level": "L0_test"
      },
      {
        "pack": "configs/test/token_set_smoke",
        "primary_level": "L1_attention"
      },
      {
        "pack": "configs/test/token_transfer_a",
        "primary_level": "L0_transfer"
      },
      {
        "pack": "configs/test/token_transfer_b",
        "primary_level": "L0_transfer"
      },
      {
        "pack": "configs/test/token_transfer_c",
        "primary_level": "L0_transfer"
      },
      {
        "pack": "configs/test/vfs_bar_access",
        "primary_level": "L0_bars"
      },
      {
        "pack": "configs/test/vfs_dependency_chain",
        "primary_level": "L0_deps"
      },
      {
        "pack": "configs/trial002_money_log_gdp",
        "primary_level": "L0_simple"
      },
      {
        "pack": "configs/trial_k_cold",
        "primary_level": "L0_cold"
      }
    ],
    "resets": [
      {
        "action": 9,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L5_multi_agent",
        "num_agents": 4,
        "pack": "configs/L5_multi_agent",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 14,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L0_0_minimal",
        "num_agents": 4,
        "pack": "configs/default_curriculum",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 14,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L0_5_dual_resource",
        "num_agents": 4,
        "pack": "configs/default_curriculum",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 14,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L1_full_observability",
        "num_agents": 4,
        "pack": "configs/default_curriculum",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 14,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L2_partial_observability",
        "num_agents": 4,
        "pack": "configs/default_curriculum",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 14,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L3_temporal_mechanics",
        "num_agents": 4,
        "pack": "configs/default_curriculum",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 14,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L1_full_observability",
        "num_agents": 4,
        "pack": "configs/differential/boundary_wrap",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 16,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L2_partial_observability",
        "num_agents": 4,
        "pack": "configs/differential/div003_cubic_partial",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 14,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L1_full_observability",
        "num_agents": 4,
        "pack": "configs/differential/div003_rect",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 8,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L0_effects",
        "num_agents": 4,
        "pack": "configs/test/effects_smoke",
        "seed": 42,
        "steps": 3
      },
      {
        "action": 12,
        "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
        "level": "L0_smoke",
        "num_agents": 4,
        "pack": "configs/test/items_smoke",
        "seed": 42,
        "steps": 3
      }
    ],
    "source_commit": "880f9c90f65aa646a0da04d7ca2ef92e48f85caa",
    "traces": [
      {
        "cell_id": "default_curriculum:L0_0_minimal:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L0_0_minimal",
          "num_agents": 4,
          "pack": "configs/default_curriculum",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "default_curriculum:L0_5_dual_resource:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L0_5_dual_resource",
          "num_agents": 4,
          "pack": "configs/default_curriculum",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "default_curriculum:L1_full_observability:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L1_full_observability",
          "num_agents": 4,
          "pack": "configs/default_curriculum",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "default_curriculum:L2_partial_observability:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L2_partial_observability",
          "num_agents": 4,
          "pack": "configs/default_curriculum",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "default_curriculum:L3_temporal_mechanics:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L3_temporal_mechanics",
          "num_agents": 4,
          "pack": "configs/default_curriculum",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "boundary_wrap:L1_full_observability:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L1_full_observability",
          "num_agents": 4,
          "pack": "configs/differential/boundary_wrap",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "div003_cubic_partial:L2_partial_observability:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L2_partial_observability",
          "num_agents": 4,
          "pack": "configs/differential/div003_cubic_partial",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "div003_rect:L1_full_observability:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L1_full_observability",
          "num_agents": 4,
          "pack": "configs/differential/div003_rect",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "items_smoke:L0_smoke:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L0_smoke",
          "num_agents": 4,
          "pack": "configs/test/items_smoke",
          "seed": 42,
          "steps": 100
        }
      },
      {
        "cell_id": "effects_smoke:L0_effects:cpu:seed42",
        "params": {
          "device": "cpu",
          "level": "L0_effects",
          "num_agents": 4,
          "pack": "configs/test/effects_smoke",
          "seed": 42,
          "steps": 100
        }
      }
    ]
  },
  "static_report": {
    "baseline_source": "880f9c90f65aa646a0da04d7ca2ef92e48f85caa",
    "case_count": 31,
    "changes": [],
    "cpu_count": 10,
    "qualified": false,
    "reading_count": 884,
    "reset_count": 11,
    "reset_failed": false,
    "source_commit": "8e3ca306d6f615bd272bb1c8d51b071b74686877",
    "stale_attributions": [],
    "trace_failed": true,
    "unattributed": []
  },
  "frozen_report": {
    "meta": {
      "oracle_ref": "oracle-2026-08-17",
      "oracle_commit": "4222a9176e68e232a0e46c7004183440e27f22c3",
      "new_commit": "8e3ca306d6f615bd272bb1c8d51b071b74686877",
      "new_dirty": true,
      "generated": "20261002-090009"
    },
    "adjudication_note": "A cell passes only as AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its known-divergences entry in register_refs. DIVERGED_AS_REGISTERED requires meeting every condition of exactly one of the three shapes below. Shape 1 (old-side-crash): old side crashed (nonzero exit) leaving no trace, with the registered signature inside the final exception text of its stderr; new side ran and produced a trace valid for the cell's own params from the declared src root. Shape 2 (hash-only): both sides ran, EXACTLY the enumerated provenance hashes differ \u2014 no more, no fewer \u2014 and every trace stream matches byte-for-byte. Shape 3 (stream-scoped): both sides ran, EXACTLY the enumerated trace streams diverge \u2014 shape changes included \u2014 and every other stream matches byte-for-byte. Everything else fails the run \u2014 an old-side failure without the signature or without a traceback, a non-crash failure, a crash that still wrote a trace, a registered divergence whose new side also fails (not yet built), a registered divergence that fails to manifest (REGISTERED_DIVERGENCE_ABSENT: stale register entry), and an all-SKIPPED run. A DIVERGE or HASH_MISMATCH with empty register_refs is a rebuild defect or a missing register entry. See docs/oracle/known-divergences.md.",
    "verdicts": [
      {
        "kind": "DIVERGED_AS_REGISTERED",
        "cell_id": "default_curriculum:L0_0_minimal:cpu:seed42",
        "detail": {
          "shape": "hash+stream",
          "mismatched": {
            "actions_hash": {
              "old": "d1be5503dde776c44f3f28d9a9d078f5f7141011829e39ad8741056a6267a18e",
              "new": "e0c20f212f05f3b36ee4f9ebb09a9b8c22b6b05b029d005d60af4fc721dc7f52"
            },
            "affordances_hash": {
              "old": "af020ccd0e9f8754dcaf7425a163276859bdb00ae1f2584c27f970f48b25a341",
              "new": "2bda63f6ad0e919402a1d8d84b1765a32874e65b0b959bea7321b00e8310f342"
            },
            "brain_hash": {
              "old": "11141093b33e94301b6fe7433340e708eef29791c7066a0242d040f812529464",
              "new": "e8092ac6be543f7546e7ae557ce23bb369efb977c84ebbb3bddd94581a8fe733"
            },
            "environment_hash": {
              "old": "6788982a4510f0e2d284f2df1e247a057eabe6e78a3a58494cc04efb79d99730",
              "new": "2accfd2d6c800f3a9711d447e910616eff9d41d35542c2739c81cf398cdcea41"
            },
            "layout_hash": {
              "old": "<absent>",
              "new": "73b4f0737c49968989902be09f8fa9370e535f596cbfafaeabed6ab7a7f34cbd"
            },
            "observation_schema_hash": {
              "old": "49374fe7ad318ffdfd12a43a6ad6067e16b0335fd4ff2b3aab57412a19896671",
              "new": "fc5c16545025dd4346ea72d0ef367429bee48e8221feef732c36bd8bb86010b9"
            },
            "pack_brain_hash": {
              "old": "<absent>",
              "new": "e8092ac6be543f7546e7ae557ce23bb369efb977c84ebbb3bddd94581a8fe733"
            },
            "stratum_hash": {
              "old": "b48070cf243e5ed77d726c7c2788aa1a3d69ed52cd3658ee77749970472ac7ce",
              "new": "bcbf09eb619adbe99423ece90163587b733825e68f75ac9184e84c8668cd6336"
            },
            "token_type_schema_hash": {
              "old": "<absent>",
              "new": "8ad2b59b502a905bf1a60f2e5743cac2c1f705f4a4143f5daf20bece38036d7d"
            },
            "transition_graph_hash": {
              "old": "e2047c67013a05c460b8b41514fd3ed18183601e4fc935ef41673b9a74ff8da8",
              "new": "27ed69c36b5a0c77e8647f0dc0d96f6f491c04eb6952f92c959de68f8c90f496"
            },
            "variable_schema_hash": {
              "old": "f28f84faba9130bb789fbc52d1a746450895187eccd7a27b6c10423a74a76fde",
              "new": "65564174ed8f79ff09e9d7db5b0f3d939717084611a3d314f2f810c7148402c7"
            },
            "vfs_hash": {
              "old": "2504f3def1bb4931c415ad3dcbc23ce14ac209338910960b49c3ec6ca7f14bf5",
              "new": "e66a0d1969376e6cf66ac3390535cee8c6bf6747975f1d40b34435e92cb3a157"
            }
          },
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                120
              ],
              "new_shape": [
                4,
                118
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            }
          }
        },
        "register_refs": [
          "DIV-009",
          "DIV-010",
          "DIV-012",
          "DIV-008",
          "DIV-014",
          "DIV-015"
        ]
      },
      {
        "kind": "DIVERGED_AS_REGISTERED",
        "cell_id": "default_curriculum:L0_5_dual_resource:cpu:seed42",
        "detail": {
          "shape": "hash+stream",
          "mismatched": {
            "actions_hash": {
              "old": "d1be5503dde776c44f3f28d9a9d078f5f7141011829e39ad8741056a6267a18e",
              "new": "e0c20f212f05f3b36ee4f9ebb09a9b8c22b6b05b029d005d60af4fc721dc7f52"
            },
            "affordances_hash": {
              "old": "af020ccd0e9f8754dcaf7425a163276859bdb00ae1f2584c27f970f48b25a341",
              "new": "2bda63f6ad0e919402a1d8d84b1765a32874e65b0b959bea7321b00e8310f342"
            },
            "brain_hash": {
              "old": "5650add3779632345e815ef6ac8883961875255679eaa92bf22a62a19ecf29aa",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "environment_hash": {
              "old": "6788982a4510f0e2d284f2df1e247a057eabe6e78a3a58494cc04efb79d99730",
              "new": "2accfd2d6c800f3a9711d447e910616eff9d41d35542c2739c81cf398cdcea41"
            },
            "layout_hash": {
              "old": "<absent>",
              "new": "73b4f0737c49968989902be09f8fa9370e535f596cbfafaeabed6ab7a7f34cbd"
            },
            "observation_schema_hash": {
              "old": "49374fe7ad318ffdfd12a43a6ad6067e16b0335fd4ff2b3aab57412a19896671",
              "new": "fc5c16545025dd4346ea72d0ef367429bee48e8221feef732c36bd8bb86010b9"
            },
            "pack_brain_hash": {
              "old": "<absent>",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "stratum_hash": {
              "old": "b48070cf243e5ed77d726c7c2788aa1a3d69ed52cd3658ee77749970472ac7ce",
              "new": "bcbf09eb619adbe99423ece90163587b733825e68f75ac9184e84c8668cd6336"
            },
            "token_type_schema_hash": {
              "old": "<absent>",
              "new": "8ad2b59b502a905bf1a60f2e5743cac2c1f705f4a4143f5daf20bece38036d7d"
            },
            "transition_graph_hash": {
              "old": "e2047c67013a05c460b8b41514fd3ed18183601e4fc935ef41673b9a74ff8da8",
              "new": "27ed69c36b5a0c77e8647f0dc0d96f6f491c04eb6952f92c959de68f8c90f496"
            },
            "variable_schema_hash": {
              "old": "f28f84faba9130bb789fbc52d1a746450895187eccd7a27b6c10423a74a76fde",
              "new": "65564174ed8f79ff09e9d7db5b0f3d939717084611a3d314f2f810c7148402c7"
            },
            "vfs_hash": {
              "old": "fcd6479026912090419813f71b25f5cce29d3a69afd9f6d158e32dc47332344e",
              "new": "4998d9d1afc55bb3b522b8f1944f3960e3555aa39986658ca02c86f2e8b24250"
            }
          },
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                120
              ],
              "new_shape": [
                4,
                118
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            }
          }
        },
        "register_refs": [
          "DIV-009",
          "DIV-010",
          "DIV-012",
          "DIV-008",
          "DIV-014",
          "DIV-015"
        ]
      },
      {
        "kind": "DIVERGED_AS_REGISTERED",
        "cell_id": "default_curriculum:L1_full_observability:cpu:seed42",
        "detail": {
          "shape": "hash+stream",
          "mismatched": {
            "actions_hash": {
              "old": "d1be5503dde776c44f3f28d9a9d078f5f7141011829e39ad8741056a6267a18e",
              "new": "e0c20f212f05f3b36ee4f9ebb09a9b8c22b6b05b029d005d60af4fc721dc7f52"
            },
            "affordances_hash": {
              "old": "af020ccd0e9f8754dcaf7425a163276859bdb00ae1f2584c27f970f48b25a341",
              "new": "2bda63f6ad0e919402a1d8d84b1765a32874e65b0b959bea7321b00e8310f342"
            },
            "brain_hash": {
              "old": "5650add3779632345e815ef6ac8883961875255679eaa92bf22a62a19ecf29aa",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "environment_hash": {
              "old": "6788982a4510f0e2d284f2df1e247a057eabe6e78a3a58494cc04efb79d99730",
              "new": "2accfd2d6c800f3a9711d447e910616eff9d41d35542c2739c81cf398cdcea41"
            },
            "layout_hash": {
              "old": "<absent>",
              "new": "73b4f0737c49968989902be09f8fa9370e535f596cbfafaeabed6ab7a7f34cbd"
            },
            "observation_schema_hash": {
              "old": "49374fe7ad318ffdfd12a43a6ad6067e16b0335fd4ff2b3aab57412a19896671",
              "new": "fc5c16545025dd4346ea72d0ef367429bee48e8221feef732c36bd8bb86010b9"
            },
            "pack_brain_hash": {
              "old": "<absent>",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "stratum_hash": {
              "old": "b48070cf243e5ed77d726c7c2788aa1a3d69ed52cd3658ee77749970472ac7ce",
              "new": "bcbf09eb619adbe99423ece90163587b733825e68f75ac9184e84c8668cd6336"
            },
            "token_type_schema_hash": {
              "old": "<absent>",
              "new": "8ad2b59b502a905bf1a60f2e5743cac2c1f705f4a4143f5daf20bece38036d7d"
            },
            "transition_graph_hash": {
              "old": "e2047c67013a05c460b8b41514fd3ed18183601e4fc935ef41673b9a74ff8da8",
              "new": "27ed69c36b5a0c77e8647f0dc0d96f6f491c04eb6952f92c959de68f8c90f496"
            },
            "variable_schema_hash": {
              "old": "f28f84faba9130bb789fbc52d1a746450895187eccd7a27b6c10423a74a76fde",
              "new": "65564174ed8f79ff09e9d7db5b0f3d939717084611a3d314f2f810c7148402c7"
            },
            "vfs_hash": {
              "old": "fcd6479026912090419813f71b25f5cce29d3a69afd9f6d158e32dc47332344e",
              "new": "4998d9d1afc55bb3b522b8f1944f3960e3555aa39986658ca02c86f2e8b24250"
            }
          },
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                120
              ],
              "new_shape": [
                4,
                118
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            }
          }
        },
        "register_refs": [
          "DIV-009",
          "DIV-010",
          "DIV-012",
          "DIV-008",
          "DIV-014",
          "DIV-015"
        ]
      },
      {
        "kind": "DIVERGED_AS_REGISTERED",
        "cell_id": "default_curriculum:L2_partial_observability:cpu:seed42",
        "detail": {
          "shape": "hash+stream",
          "mismatched": {
            "actions_hash": {
              "old": "d1be5503dde776c44f3f28d9a9d078f5f7141011829e39ad8741056a6267a18e",
              "new": "e0c20f212f05f3b36ee4f9ebb09a9b8c22b6b05b029d005d60af4fc721dc7f52"
            },
            "affordances_hash": {
              "old": "af020ccd0e9f8754dcaf7425a163276859bdb00ae1f2584c27f970f48b25a341",
              "new": "2bda63f6ad0e919402a1d8d84b1765a32874e65b0b959bea7321b00e8310f342"
            },
            "brain_hash": {
              "old": "5650add3779632345e815ef6ac8883961875255679eaa92bf22a62a19ecf29aa",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "environment_hash": {
              "old": "6788982a4510f0e2d284f2df1e247a057eabe6e78a3a58494cc04efb79d99730",
              "new": "2accfd2d6c800f3a9711d447e910616eff9d41d35542c2739c81cf398cdcea41"
            },
            "layout_hash": {
              "old": "<absent>",
              "new": "73b4f0737c49968989902be09f8fa9370e535f596cbfafaeabed6ab7a7f34cbd"
            },
            "observation_schema_hash": {
              "old": "acf885d166176302417096cc5e38dd483b770f7f324c4fc6e8236dec132bc48c",
              "new": "fc5c16545025dd4346ea72d0ef367429bee48e8221feef732c36bd8bb86010b9"
            },
            "pack_brain_hash": {
              "old": "<absent>",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "stratum_hash": {
              "old": "b48070cf243e5ed77d726c7c2788aa1a3d69ed52cd3658ee77749970472ac7ce",
              "new": "bcbf09eb619adbe99423ece90163587b733825e68f75ac9184e84c8668cd6336"
            },
            "token_type_schema_hash": {
              "old": "<absent>",
              "new": "8ad2b59b502a905bf1a60f2e5743cac2c1f705f4a4143f5daf20bece38036d7d"
            },
            "transition_graph_hash": {
              "old": "e2047c67013a05c460b8b41514fd3ed18183601e4fc935ef41673b9a74ff8da8",
              "new": "27ed69c36b5a0c77e8647f0dc0d96f6f491c04eb6952f92c959de68f8c90f496"
            },
            "variable_schema_hash": {
              "old": "f28f84faba9130bb789fbc52d1a746450895187eccd7a27b6c10423a74a76fde",
              "new": "65564174ed8f79ff09e9d7db5b0f3d939717084611a3d314f2f810c7148402c7"
            },
            "vfs_hash": {
              "old": "24f6eef8553a2caf523e2be5fa4b0409ddabdf2e9f18e9b106d3775839db4821",
              "new": "4998d9d1afc55bb3b522b8f1944f3960e3555aa39986658ca02c86f2e8b24250"
            }
          },
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                120
              ],
              "new_shape": [
                4,
                118
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            }
          }
        },
        "register_refs": [
          "DIV-009",
          "DIV-010",
          "DIV-012",
          "DIV-008",
          "DIV-014",
          "DIV-015"
        ]
      },
      {
        "kind": "DIVERGED_AS_REGISTERED",
        "cell_id": "default_curriculum:L3_temporal_mechanics:cpu:seed42",
        "detail": {
          "shape": "hash+stream",
          "mismatched": {
            "actions_hash": {
              "old": "d1be5503dde776c44f3f28d9a9d078f5f7141011829e39ad8741056a6267a18e",
              "new": "e0c20f212f05f3b36ee4f9ebb09a9b8c22b6b05b029d005d60af4fc721dc7f52"
            },
            "affordances_hash": {
              "old": "af020ccd0e9f8754dcaf7425a163276859bdb00ae1f2584c27f970f48b25a341",
              "new": "2bda63f6ad0e919402a1d8d84b1765a32874e65b0b959bea7321b00e8310f342"
            },
            "brain_hash": {
              "old": "5650add3779632345e815ef6ac8883961875255679eaa92bf22a62a19ecf29aa",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "environment_hash": {
              "old": "6788982a4510f0e2d284f2df1e247a057eabe6e78a3a58494cc04efb79d99730",
              "new": "2accfd2d6c800f3a9711d447e910616eff9d41d35542c2739c81cf398cdcea41"
            },
            "layout_hash": {
              "old": "<absent>",
              "new": "73b4f0737c49968989902be09f8fa9370e535f596cbfafaeabed6ab7a7f34cbd"
            },
            "observation_schema_hash": {
              "old": "9a33b4797a764f8100f08360cf2e13c17e265e7e09e0300143ec4fe5ebb79e55",
              "new": "fc5c16545025dd4346ea72d0ef367429bee48e8221feef732c36bd8bb86010b9"
            },
            "pack_brain_hash": {
              "old": "<absent>",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "stratum_hash": {
              "old": "b48070cf243e5ed77d726c7c2788aa1a3d69ed52cd3658ee77749970472ac7ce",
              "new": "bcbf09eb619adbe99423ece90163587b733825e68f75ac9184e84c8668cd6336"
            },
            "token_type_schema_hash": {
              "old": "<absent>",
              "new": "8ad2b59b502a905bf1a60f2e5743cac2c1f705f4a4143f5daf20bece38036d7d"
            },
            "transition_graph_hash": {
              "old": "e2047c67013a05c460b8b41514fd3ed18183601e4fc935ef41673b9a74ff8da8",
              "new": "27ed69c36b5a0c77e8647f0dc0d96f6f491c04eb6952f92c959de68f8c90f496"
            },
            "variable_schema_hash": {
              "old": "f28f84faba9130bb789fbc52d1a746450895187eccd7a27b6c10423a74a76fde",
              "new": "65564174ed8f79ff09e9d7db5b0f3d939717084611a3d314f2f810c7148402c7"
            },
            "vfs_hash": {
              "old": "5d6dc6dbb3327fa46e4de700ebbbab138531b7f677552e2dc27601b93ab983ee",
              "new": "4998d9d1afc55bb3b522b8f1944f3960e3555aa39986658ca02c86f2e8b24250"
            }
          },
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                120
              ],
              "new_shape": [
                4,
                118
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            }
          }
        },
        "register_refs": [
          "DIV-009",
          "DIV-010",
          "DIV-012",
          "DIV-008",
          "DIV-014",
          "DIV-015"
        ]
      },
      {
        "kind": "SKIPPED",
        "cell_id": "default_curriculum:L0_0_minimal:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "SKIPPED",
        "cell_id": "default_curriculum:L0_5_dual_resource:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "SKIPPED",
        "cell_id": "default_curriculum:L1_full_observability:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "SKIPPED",
        "cell_id": "default_curriculum:L2_partial_observability:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "SKIPPED",
        "cell_id": "default_curriculum:L3_temporal_mechanics:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "DIVERGED_AS_REGISTERED",
        "cell_id": "boundary_wrap:L1_full_observability:cpu:seed42",
        "detail": {
          "shape": "hash+stream",
          "mismatched": {
            "actions_hash": {
              "old": "d1be5503dde776c44f3f28d9a9d078f5f7141011829e39ad8741056a6267a18e",
              "new": "e0c20f212f05f3b36ee4f9ebb09a9b8c22b6b05b029d005d60af4fc721dc7f52"
            },
            "affordances_hash": {
              "old": "af020ccd0e9f8754dcaf7425a163276859bdb00ae1f2584c27f970f48b25a341",
              "new": "2bda63f6ad0e919402a1d8d84b1765a32874e65b0b959bea7321b00e8310f342"
            },
            "brain_hash": {
              "old": "5650add3779632345e815ef6ac8883961875255679eaa92bf22a62a19ecf29aa",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "environment_hash": {
              "old": "6788982a4510f0e2d284f2df1e247a057eabe6e78a3a58494cc04efb79d99730",
              "new": "2accfd2d6c800f3a9711d447e910616eff9d41d35542c2739c81cf398cdcea41"
            },
            "layout_hash": {
              "old": "<absent>",
              "new": "73b4f0737c49968989902be09f8fa9370e535f596cbfafaeabed6ab7a7f34cbd"
            },
            "observation_schema_hash": {
              "old": "49374fe7ad318ffdfd12a43a6ad6067e16b0335fd4ff2b3aab57412a19896671",
              "new": "fc5c16545025dd4346ea72d0ef367429bee48e8221feef732c36bd8bb86010b9"
            },
            "pack_brain_hash": {
              "old": "<absent>",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "stratum_hash": {
              "old": "51d88118e2fbf9fcc4c3ef96ae978621c1ed5e3ba70df05beccc24759403ea8b",
              "new": "4a58653ad99193e46ad0f6428586a292d34c8167a98e3521b9d5c8d1f7e3cecf"
            },
            "token_type_schema_hash": {
              "old": "<absent>",
              "new": "8ad2b59b502a905bf1a60f2e5743cac2c1f705f4a4143f5daf20bece38036d7d"
            },
            "transition_graph_hash": {
              "old": "e2047c67013a05c460b8b41514fd3ed18183601e4fc935ef41673b9a74ff8da8",
              "new": "27ed69c36b5a0c77e8647f0dc0d96f6f491c04eb6952f92c959de68f8c90f496"
            },
            "variable_schema_hash": {
              "old": "f28f84faba9130bb789fbc52d1a746450895187eccd7a27b6c10423a74a76fde",
              "new": "65564174ed8f79ff09e9d7db5b0f3d939717084611a3d314f2f810c7148402c7"
            },
            "vfs_hash": {
              "old": "fcd6479026912090419813f71b25f5cce29d3a69afd9f6d158e32dc47332344e",
              "new": "4998d9d1afc55bb3b522b8f1944f3960e3555aa39986658ca02c86f2e8b24250"
            }
          },
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                120
              ],
              "new_shape": [
                4,
                118
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            }
          }
        },
        "register_refs": [
          "DIV-009",
          "DIV-010",
          "DIV-012",
          "DIV-008",
          "DIV-014",
          "DIV-015"
        ]
      },
      {
        "kind": "DIVERGED_AS_REGISTERED",
        "cell_id": "div003_cubic_partial:L2_partial_observability:cpu:seed42",
        "detail": {
          "shape": "hash+stream",
          "mismatched": {
            "actions_hash": {
              "old": "d1be5503dde776c44f3f28d9a9d078f5f7141011829e39ad8741056a6267a18e",
              "new": "e0c20f212f05f3b36ee4f9ebb09a9b8c22b6b05b029d005d60af4fc721dc7f52"
            },
            "affordances_hash": {
              "old": "af020ccd0e9f8754dcaf7425a163276859bdb00ae1f2584c27f970f48b25a341",
              "new": "2bda63f6ad0e919402a1d8d84b1765a32874e65b0b959bea7321b00e8310f342"
            },
            "brain_hash": {
              "old": "5650add3779632345e815ef6ac8883961875255679eaa92bf22a62a19ecf29aa",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "environment_hash": {
              "old": "6788982a4510f0e2d284f2df1e247a057eabe6e78a3a58494cc04efb79d99730",
              "new": "2accfd2d6c800f3a9711d447e910616eff9d41d35542c2739c81cf398cdcea41"
            },
            "layout_hash": {
              "old": "<absent>",
              "new": "36baa279dbc72741dacc0d348032dcf0b866bc2dd5d1630f33f47122a51784d8"
            },
            "observation_schema_hash": {
              "old": "0947a6db269343ca3e57179bb31efa1f89e08d037aa3fab2174eb69d02b4ccd9",
              "new": "88b72261226dccd95c5717aacefdaec0e4bbf4a2decf8b8439df80b69337cc07"
            },
            "pack_brain_hash": {
              "old": "<absent>",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "stratum_hash": {
              "old": "2fa2c88dbcad0c76d241592b77ad905597ebf11dd1ef90d3d18c029a91f5ea50",
              "new": "13ff5fa8dccea8c4940f30a3328eab28033c99cb7e7c90ab6ddc38e1c86465e8"
            },
            "token_type_schema_hash": {
              "old": "<absent>",
              "new": "8ad2b59b502a905bf1a60f2e5743cac2c1f705f4a4143f5daf20bece38036d7d"
            },
            "transition_graph_hash": {
              "old": "e2047c67013a05c460b8b41514fd3ed18183601e4fc935ef41673b9a74ff8da8",
              "new": "27ed69c36b5a0c77e8647f0dc0d96f6f491c04eb6952f92c959de68f8c90f496"
            },
            "variable_schema_hash": {
              "old": "46c4b5dfdf9f1f06bab5659adb5412b951861831553b65a83f7d391c2e2a0451",
              "new": "65564174ed8f79ff09e9d7db5b0f3d939717084611a3d314f2f810c7148402c7"
            },
            "vfs_hash": {
              "old": "81854b054308ece102b184080648385046c8ac5f445ad8de8c566fd7c1c0dff6",
              "new": "2eebe43c9510d581fc2fc2416d58d22a0c33a10c1cdf9aaf5461533d1438e5cc"
            }
          },
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                350
              ],
              "new_shape": [
                4,
                152
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            }
          }
        },
        "register_refs": [
          "DIV-009",
          "DIV-010",
          "DIV-012",
          "DIV-008",
          "DIV-014",
          "DIV-015"
        ]
      },
      {
        "kind": "DIVERGED_AS_REGISTERED",
        "cell_id": "div003_rect:L1_full_observability:cpu:seed42",
        "detail": {
          "shape": "hash+stream",
          "mismatched": {
            "actions_hash": {
              "old": "d1be5503dde776c44f3f28d9a9d078f5f7141011829e39ad8741056a6267a18e",
              "new": "e0c20f212f05f3b36ee4f9ebb09a9b8c22b6b05b029d005d60af4fc721dc7f52"
            },
            "affordances_hash": {
              "old": "af020ccd0e9f8754dcaf7425a163276859bdb00ae1f2584c27f970f48b25a341",
              "new": "2bda63f6ad0e919402a1d8d84b1765a32874e65b0b959bea7321b00e8310f342"
            },
            "brain_hash": {
              "old": "5650add3779632345e815ef6ac8883961875255679eaa92bf22a62a19ecf29aa",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "environment_hash": {
              "old": "6788982a4510f0e2d284f2df1e247a057eabe6e78a3a58494cc04efb79d99730",
              "new": "2accfd2d6c800f3a9711d447e910616eff9d41d35542c2739c81cf398cdcea41"
            },
            "layout_hash": {
              "old": "<absent>",
              "new": "73b4f0737c49968989902be09f8fa9370e535f596cbfafaeabed6ab7a7f34cbd"
            },
            "observation_schema_hash": {
              "old": "6f48eb08ae8dfc1edee9c495cafff172406021356022b370731963ae6761aedc",
              "new": "fc5c16545025dd4346ea72d0ef367429bee48e8221feef732c36bd8bb86010b9"
            },
            "pack_brain_hash": {
              "old": "<absent>",
              "new": "4f10939daf7a1bbd23ab0084fed2f7bc4da18bcc6993d092c2aded1a64b9125f"
            },
            "stratum_hash": {
              "old": "54f8b289cd06e04888d3aeb80783e72339c0c126fdb3c3269df6760c5344628f",
              "new": "5db2b56880384f2de6767177b48d8dc3ff4d5fb8fac05d67e9c26739a3aa2176"
            },
            "token_type_schema_hash": {
              "old": "<absent>",
              "new": "8ad2b59b502a905bf1a60f2e5743cac2c1f705f4a4143f5daf20bece38036d7d"
            },
            "transition_graph_hash": {
              "old": "e2047c67013a05c460b8b41514fd3ed18183601e4fc935ef41673b9a74ff8da8",
              "new": "27ed69c36b5a0c77e8647f0dc0d96f6f491c04eb6952f92c959de68f8c90f496"
            },
            "variable_schema_hash": {
              "old": "a591d7654400f16aee2b0d1967e27332ee1aff5397e7e667459c3488c3dab7c1",
              "new": "65564174ed8f79ff09e9d7db5b0f3d939717084611a3d314f2f810c7148402c7"
            },
            "vfs_hash": {
              "old": "eab17e61316f9a89f972a199941c9d097a8f2050398cd6fa0c817d0ca8395552",
              "new": "4998d9d1afc55bb3b522b8f1944f3960e3555aa39986658ca02c86f2e8b24250"
            }
          },
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                104
              ],
              "new_shape": [
                4,
                118
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            }
          }
        },
        "register_refs": [
          "DIV-009",
          "DIV-010",
          "DIV-012",
          "DIV-008",
          "DIV-014",
          "DIV-015"
        ]
      },
      {
        "kind": "SKIPPED",
        "cell_id": "boundary_wrap:L1_full_observability:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "SKIPPED",
        "cell_id": "div003_cubic_partial:L2_partial_observability:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "SKIPPED",
        "cell_id": "div003_rect:L1_full_observability:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "DIVERGE",
        "cell_id": "items_smoke:L0_smoke:cpu:seed42",
        "detail": {
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                61
              ],
              "new_shape": [
                4,
                474
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            },
            "rewards": {
              "step": 99,
              "shape_changed": false,
              "indices": [
                [
                  0
                ],
                [
                  1
                ],
                [
                  3
                ]
              ],
              "diff_count": 3,
              "max_abs_diff": 1.0,
              "diff_entries": 1
            }
          },
          "undeclared_streams": [
            "rewards"
          ],
          "declared_streams": [
            "obs"
          ]
        },
        "register_refs": []
      },
      {
        "kind": "DIVERGE",
        "cell_id": "effects_smoke:L0_effects:cpu:seed42",
        "detail": {
          "streams": {
            "obs": {
              "step": 0,
              "shape_changed": true,
              "old_shape": [
                4,
                59
              ],
              "new_shape": [
                4,
                61
              ],
              "old_dtype": "float32",
              "new_dtype": "float32",
              "diff_entries": 101
            },
            "rewards": {
              "step": 99,
              "shape_changed": false,
              "indices": [
                [
                  0
                ],
                [
                  1
                ],
                [
                  2
                ],
                [
                  3
                ]
              ],
              "diff_count": 4,
              "max_abs_diff": 1.0,
              "diff_entries": 1
            }
          },
          "undeclared_streams": [
            "rewards"
          ],
          "declared_streams": [
            "obs"
          ]
        },
        "register_refs": []
      },
      {
        "kind": "SKIPPED",
        "cell_id": "items_smoke:L0_smoke:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      },
      {
        "kind": "SKIPPED",
        "cell_id": "effects_smoke:L0_effects:cuda:seed42",
        "detail": {
          "reason": "cuda not requested"
        },
        "register_refs": []
      }
    ]
  },
  "config_sha256": {
    "configs/L5_multi_agent/actions.yaml": "c98d76e064dce68b4c51031904f632ac21b651eaee92f2c0d4661ce14fdd15ef",
    "configs/L5_multi_agent/brain.yaml": "f30d887c4f2113789c18ac615fd6cb3fdb48c90297e99df6be6070b327e2829a",
    "configs/L5_multi_agent/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/L5_multi_agent/environment.yaml": "641115efdd5cfcd5071744d2bda3feaebcbf7fce1c2ed594f00f84a69b22a83a",
    "configs/L5_multi_agent/experiment.yaml": "81c27e9aa0a78bdb54a2268f6b32b53fe30de2d3836ab5e334609abe73c11d96",
    "configs/L5_multi_agent/items.yaml": "672b1199f237dd05bc25f8d4540df7e4f037bbfbb060af1a6e5a344228347166",
    "configs/L5_multi_agent/levels/L5_multi_agent/affordances.yaml": "eb2a53f4a27a9e4a349721eeef9bf08afad161904e9d02292e21c8312978b362",
    "configs/L5_multi_agent/levels/L5_multi_agent/bars.yaml": "9e952c17d9bb941a9a9d37c4e7041001f41ed311838fb1c9876ea7a9d6b8e06c",
    "configs/L5_multi_agent/levels/L5_multi_agent/curriculum.yaml": "76b6305e34873217c261bc63d095f3505fc8ae93fe5e14857d123846d82308bf",
    "configs/L5_multi_agent/levels/L5_multi_agent/drive.yaml": "b139146a9e6ae743893ad835ff4d9b0ee1b2971a9d7f4d246f3cc50fbd154136",
    "configs/L5_multi_agent/levels/L5_multi_agent/training.yaml": "e2add40c4879fdd32d72b95a18d3ec0d20ee9f20d9713701f86e149add7a3da0",
    "configs/L5_multi_agent/stratum.yaml": "4c6a37e6e20d296906dff71d437411a0b0b61bc34e8880754c3ca87516a75958",
    "configs/L5_multi_agent/variables.yaml": "e12de1d027b2d6195d38262a019c06eb20479918c2ef606cd9931ecc5fde33fc",
    "configs/aspatial_test/actions.yaml": "d9f4ae5d0f39422d2a2752c6b832387a522b970bb9d2fe2958e21a0fbbba6b08",
    "configs/aspatial_test/brain.yaml": "222e7b8a1341ed58bb784421b239f17ffa4204dc6f02ae222ce249193a4e43ee",
    "configs/aspatial_test/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/aspatial_test/environment.yaml": "f81ed6fe2b1a44a33b81ee4141c5c2d1a75149383b8e2f60115530c6a0a2c4ba",
    "configs/aspatial_test/experiment.yaml": "518589d2164be7126be79d13d7a69a5bc024f3c4c0b4a896291dce43a38416d8",
    "configs/aspatial_test/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/aspatial_test/levels/L0/affordances.yaml": "b76f46b120ad02c9b1249920c8770c2ddb01da9f376aa33c65a7fd53e37dfaf3",
    "configs/aspatial_test/levels/L0/bars.yaml": "c707622784d58c08d79eab895c2232a7d58b02a0fd40dbc783d728d1467e78f0",
    "configs/aspatial_test/levels/L0/curriculum.yaml": "d77d937b25d33c9c2d1cbf62c9b5a48a0e645f299fa7ccf639c11055cde502f5",
    "configs/aspatial_test/levels/L0/drive.yaml": "b07f4bc73081a12be1d0124374ee99e793188b1c341bab8302ae4ebf11442feb",
    "configs/aspatial_test/levels/L0/training.yaml": "9680798f818416d5578b1bdd0a5dcb005392726508e77614774e217a405920f2",
    "configs/aspatial_test/stratum.yaml": "291e2403a4b23262061dd4a0bae5219f0e1f3d6a60fe3d958dbfced67ed735eb",
    "configs/aspatial_test/variables.yaml": "bf717444ec20cf907edaf3a24809764b6c209605445740431779379edcb0f475",
    "configs/benchmarks/l2_token_regression/brain_templates/token_feedforward_attention.yaml": "d17bfaccdc8becd5e8289b29ef240eadc4175188a559acc15309aae6e110bbe5",
    "configs/benchmarks/l2_token_regression/brain_templates/token_feedforward_mean.yaml": "bc262f464ff7ca4e15a3e3f23e936fc08e9601852465771b17de48e82e623411",
    "configs/benchmarks/l2_token_regression/brain_templates/token_recurrent_attention.yaml": "c5b843d4ebb3bf92d131f47f22f3801f3cbdca385a1df3d312fd729ceca68c7a",
    "configs/benchmarks/l2_token_regression/brain_templates/token_recurrent_mean.yaml": "bb47b2964e6323283dc8ac41cf872a99eda3301602b0f62f480308319ef935bd",
    "configs/default_curriculum/actions.yaml": "5f94d0b8c4b2d10beffd479b43e1d21a95d5601d46dcd034931e73f0e0cd45be",
    "configs/default_curriculum/brain.yaml": "6beae4fd3e47613042f7ae533a462c62fdb468e80315b718bdc73d9e852a152b",
    "configs/default_curriculum/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/default_curriculum/environment.yaml": "27e30e134a5aff505790cbaea53bdca52b60bf7303171e7e1f91f9fe8d94f2ee",
    "configs/default_curriculum/experiment.yaml": "977a8c2273d757033cf63b9e29c3c943c516e2f6556874914203e124e67ca9b3",
    "configs/default_curriculum/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/default_curriculum/levels/L0_0_minimal/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/default_curriculum/levels/L0_0_minimal/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/default_curriculum/levels/L0_0_minimal/curriculum.yaml": "e24d6f042e667615359ff43b8c6e2c84982695bfcd6c8ed5795f48a2eb3201e8",
    "configs/default_curriculum/levels/L0_0_minimal/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/default_curriculum/levels/L0_0_minimal/training.yaml": "4065173cf7651dc34d1b781d70b46ffb1930f7f720532ce9aeb449a832f000db",
    "configs/default_curriculum/levels/L0_5_dual_resource/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/default_curriculum/levels/L0_5_dual_resource/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/default_curriculum/levels/L0_5_dual_resource/curriculum.yaml": "4fe63e0ff053cb2e6aebcfc7b8518e104c0809ec9394e16df2b5d546d41591d3",
    "configs/default_curriculum/levels/L0_5_dual_resource/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/default_curriculum/levels/L0_5_dual_resource/training.yaml": "933012c628b741083e9153d70a3c0e99dca6a4d95ef88644c133d21a3c45c9bf",
    "configs/default_curriculum/levels/L1_full_observability/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/default_curriculum/levels/L1_full_observability/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/default_curriculum/levels/L1_full_observability/curriculum.yaml": "fc41e113e7ca1d9a588a608a431fb6a6bb0cc02f422faad927201a6164b72243",
    "configs/default_curriculum/levels/L1_full_observability/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/default_curriculum/levels/L1_full_observability/training.yaml": "398fe080467e4cfb63bcb09562f095254fbbe5c5bfce913b129b6a796aa88c3c",
    "configs/default_curriculum/levels/L2_partial_observability/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/default_curriculum/levels/L2_partial_observability/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/default_curriculum/levels/L2_partial_observability/curriculum.yaml": "219785448971fea947685c45b5044904096bb102b331b99496ad7b7e44cfc795",
    "configs/default_curriculum/levels/L2_partial_observability/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/default_curriculum/levels/L2_partial_observability/training.yaml": "cf399a8bacaa77df2498c1bc5fcf34367d409fec7c0e56d1fb3b6bf3ab8e43eb",
    "configs/default_curriculum/levels/L3_temporal_mechanics/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/default_curriculum/levels/L3_temporal_mechanics/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/default_curriculum/levels/L3_temporal_mechanics/curriculum.yaml": "51bc9217952ee8df8e90ea368d6a14093604f504234fdad65e56f3a7999d649f",
    "configs/default_curriculum/levels/L3_temporal_mechanics/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/default_curriculum/levels/L3_temporal_mechanics/training.yaml": "7e497eccaf86e04a6fd158898eefbd26822d329b5df14963dbf64b90e61aa87b",
    "configs/default_curriculum/stratum.yaml": "740d99ed47564a8e8825cae83c1c03601715dc7d1ea70dbb458162bed165a545",
    "configs/default_curriculum/variables.yaml": "a2192f836f2de11a35ac4a5491fd9fd2de9c62feca7a73418f15137a0ed6acf9",
    "configs/differential/boundary_wrap/actions.yaml": "5f94d0b8c4b2d10beffd479b43e1d21a95d5601d46dcd034931e73f0e0cd45be",
    "configs/differential/boundary_wrap/brain.yaml": "6beae4fd3e47613042f7ae533a462c62fdb468e80315b718bdc73d9e852a152b",
    "configs/differential/boundary_wrap/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/differential/boundary_wrap/environment.yaml": "27e30e134a5aff505790cbaea53bdca52b60bf7303171e7e1f91f9fe8d94f2ee",
    "configs/differential/boundary_wrap/experiment.yaml": "1829465bc15754e596aca3994b8e4ade82a31143e65e610e9dc53410e0e6680a",
    "configs/differential/boundary_wrap/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/differential/boundary_wrap/levels/L1_full_observability/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/differential/boundary_wrap/levels/L1_full_observability/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/differential/boundary_wrap/levels/L1_full_observability/curriculum.yaml": "fc41e113e7ca1d9a588a608a431fb6a6bb0cc02f422faad927201a6164b72243",
    "configs/differential/boundary_wrap/levels/L1_full_observability/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/differential/boundary_wrap/levels/L1_full_observability/training.yaml": "398fe080467e4cfb63bcb09562f095254fbbe5c5bfce913b129b6a796aa88c3c",
    "configs/differential/boundary_wrap/stratum.yaml": "b516656ecca108758df3152e0d96a312c94a674a4726018f8983b905849cdd4d",
    "configs/differential/boundary_wrap/variables.yaml": "a2192f836f2de11a35ac4a5491fd9fd2de9c62feca7a73418f15137a0ed6acf9",
    "configs/differential/div003_cubic_partial/actions.yaml": "5f94d0b8c4b2d10beffd479b43e1d21a95d5601d46dcd034931e73f0e0cd45be",
    "configs/differential/div003_cubic_partial/brain.yaml": "6beae4fd3e47613042f7ae533a462c62fdb468e80315b718bdc73d9e852a152b",
    "configs/differential/div003_cubic_partial/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/differential/div003_cubic_partial/environment.yaml": "27e30e134a5aff505790cbaea53bdca52b60bf7303171e7e1f91f9fe8d94f2ee",
    "configs/differential/div003_cubic_partial/experiment.yaml": "76431c5522b363bcfdbc9701f10647a38dbca2234386a350fedb84fc60312e6d",
    "configs/differential/div003_cubic_partial/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/differential/div003_cubic_partial/levels/L2_partial_observability/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/differential/div003_cubic_partial/levels/L2_partial_observability/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/differential/div003_cubic_partial/levels/L2_partial_observability/curriculum.yaml": "219785448971fea947685c45b5044904096bb102b331b99496ad7b7e44cfc795",
    "configs/differential/div003_cubic_partial/levels/L2_partial_observability/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/differential/div003_cubic_partial/levels/L2_partial_observability/training.yaml": "cf399a8bacaa77df2498c1bc5fcf34367d409fec7c0e56d1fb3b6bf3ab8e43eb",
    "configs/differential/div003_cubic_partial/stratum.yaml": "bf3b7b7ad0582944fd9b769d83f3e6a540f6cb9e56f6cdde4115fb54326f1845",
    "configs/differential/div003_cubic_partial/variables.yaml": "a2192f836f2de11a35ac4a5491fd9fd2de9c62feca7a73418f15137a0ed6acf9",
    "configs/differential/div003_rect/actions.yaml": "5f94d0b8c4b2d10beffd479b43e1d21a95d5601d46dcd034931e73f0e0cd45be",
    "configs/differential/div003_rect/brain.yaml": "6beae4fd3e47613042f7ae533a462c62fdb468e80315b718bdc73d9e852a152b",
    "configs/differential/div003_rect/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/differential/div003_rect/environment.yaml": "27e30e134a5aff505790cbaea53bdca52b60bf7303171e7e1f91f9fe8d94f2ee",
    "configs/differential/div003_rect/experiment.yaml": "76338b67a5dc33682a5f68d6897b6b5babb03aceaf87333bc3098b7bf2670756",
    "configs/differential/div003_rect/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/differential/div003_rect/levels/L1_full_observability/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/differential/div003_rect/levels/L1_full_observability/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/differential/div003_rect/levels/L1_full_observability/curriculum.yaml": "fc41e113e7ca1d9a588a608a431fb6a6bb0cc02f422faad927201a6164b72243",
    "configs/differential/div003_rect/levels/L1_full_observability/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/differential/div003_rect/levels/L1_full_observability/training.yaml": "398fe080467e4cfb63bcb09562f095254fbbe5c5bfce913b129b6a796aa88c3c",
    "configs/differential/div003_rect/stratum.yaml": "772242034c34fb5dd598ff2566473d123c287a9213730b50c8645508d5d8ca3d",
    "configs/differential/div003_rect/variables.yaml": "a2192f836f2de11a35ac4a5491fd9fd2de9c62feca7a73418f15137a0ed6acf9",
    "configs/reference/config-complete.yaml": "24fa08bdb0fa3d5542c0def9f562eb7eed923d00f6f6bbfda06200dfc0b8ee00",
    "configs/reference/model_pack/actions.yaml": "11cf7da67f3e824f45a743794a9bf4f6d3eaa2229b2b6603ab6e623b8a1f6c45",
    "configs/reference/model_pack/brain.yaml": "b6249279df2cde80af2049b60bd8a43cbe8e0f2024aa66528157613eeef80a86",
    "configs/reference/model_pack/effects.yaml": "9930d2f2c8b1a007bc757f9f98531d4a27e6f1fe9e62d240efc511a2f1123549",
    "configs/reference/model_pack/environment.yaml": "d0c01ee7081a4ffcda4748a191354236194820e6684d6e1f26d9da337d73cafd",
    "configs/reference/model_pack/experiment.yaml": "96ab29544802e7746665f7917f2f513fe692675a6fda4881338060974285cc51",
    "configs/reference/model_pack/items.yaml": "5d89c74fe33c3194eaca0da6f8a1a07abccee552f2fe39af36928ae94d01c8ff",
    "configs/reference/model_pack/levels/L0_demo/affordances.yaml": "08f3310f96162ec264209dd645573a954a58a2ec79425991962fc1e85ff439c1",
    "configs/reference/model_pack/levels/L0_demo/bars.yaml": "491fb2891dfbdc66c48555bccf35cc0aea57519c5c1fdb9ae4fe1baf115f7726",
    "configs/reference/model_pack/levels/L0_demo/curriculum.yaml": "ca5c83be8116d439137cc03ad29b112e6c7f7ad0a024ab46e18354b017081586",
    "configs/reference/model_pack/levels/L0_demo/drive.yaml": "6394fb47d32069f29e5edf210361c212851fefd5a3e76c3fa4b450b930647051",
    "configs/reference/model_pack/levels/L0_demo/items.yaml": "a9e741e7e38a907720681e301282748c5cf763cc2f74d5c8e44adf272b88403e",
    "configs/reference/model_pack/levels/L0_demo/training.yaml": "1d1c6b9f3b6efdcde2adfadb870b3e9a745f0845c76446c6d6152f77195a7db3",
    "configs/reference/model_pack/stratum.yaml": "9dff7e8d8b38fd5b460276ed3a2119cae5ccdb4778c650fa235b8c2c849c5b63",
    "configs/reference/model_pack/variables.yaml": "a3eb9dc2683a163e83a7b147ac3a90f09861da262eca5c0949bdf4b4c829aec5",
    "configs/simple/actions.yaml": "c98d76e064dce68b4c51031904f632ac21b651eaee92f2c0d4661ce14fdd15ef",
    "configs/simple/brain.yaml": "ce058bee6d948b1fe2785d8f756e7630b04d7cf18abd3b7508f7ad2fe3a75fd1",
    "configs/simple/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/simple/environment.yaml": "641115efdd5cfcd5071744d2bda3feaebcbf7fce1c2ed594f00f84a69b22a83a",
    "configs/simple/experiment.yaml": "744b1e6be9bb9a12e818d57c1e473c5b9d7de9ddac9c292ce480f0591e1d6b9e",
    "configs/simple/items.yaml": "672b1199f237dd05bc25f8d4540df7e4f037bbfbb060af1a6e5a344228347166",
    "configs/simple/levels/L0_simple/affordances.yaml": "80a25aa66c19dcf6804406aea2a04a99d8fdc245a2ae0cc92c4d3a384dfcab30",
    "configs/simple/levels/L0_simple/bars.yaml": "9e952c17d9bb941a9a9d37c4e7041001f41ed311838fb1c9876ea7a9d6b8e06c",
    "configs/simple/levels/L0_simple/curriculum.yaml": "82711da489a90390ce557d5c04e133b473adca93c58e78e6785ec45243293075",
    "configs/simple/levels/L0_simple/drive.yaml": "b139146a9e6ae743893ad835ff4d9b0ee1b2971a9d7f4d246f3cc50fbd154136",
    "configs/simple/levels/L0_simple/training.yaml": "66ba12c770d99c1a79164b628e2c081d32ea939f843e8a35306455260cab3f98",
    "configs/simple/stratum.yaml": "4c6a37e6e20d296906dff71d437411a0b0b61bc34e8880754c3ca87516a75958",
    "configs/simple/variables.yaml": "373b372f5c3211944aeef4e43adb046e3b483cfbf92e217e32effc33fdfe7c90",
    "configs/static_epistemic_access/actions.yaml": "12d42b8b8052f81400be9860185dca9ec246fe138258571acada758a2e2a8e2f",
    "configs/static_epistemic_access/brain.yaml": "ce058bee6d948b1fe2785d8f756e7630b04d7cf18abd3b7508f7ad2fe3a75fd1",
    "configs/static_epistemic_access/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/static_epistemic_access/environment.yaml": "641115efdd5cfcd5071744d2bda3feaebcbf7fce1c2ed594f00f84a69b22a83a",
    "configs/static_epistemic_access/experiment.yaml": "a940490f2e1f00a5d00bcbf32f6098d827af1603531acae77ad03c4e077cc09f",
    "configs/static_epistemic_access/items.yaml": "672b1199f237dd05bc25f8d4540df7e4f037bbfbb060af1a6e5a344228347166",
    "configs/static_epistemic_access/levels/L0_simple/affordances.yaml": "80a25aa66c19dcf6804406aea2a04a99d8fdc245a2ae0cc92c4d3a384dfcab30",
    "configs/static_epistemic_access/levels/L0_simple/bars.yaml": "9e952c17d9bb941a9a9d37c4e7041001f41ed311838fb1c9876ea7a9d6b8e06c",
    "configs/static_epistemic_access/levels/L0_simple/curriculum.yaml": "82711da489a90390ce557d5c04e133b473adca93c58e78e6785ec45243293075",
    "configs/static_epistemic_access/levels/L0_simple/drive.yaml": "0e88fafa38157ad9f1a0f81b3cfb504ad8a297f5a603ebf82ec7c2f3f2a4288d",
    "configs/static_epistemic_access/levels/L0_simple/training.yaml": "66ba12c770d99c1a79164b628e2c081d32ea939f843e8a35306455260cab3f98",
    "configs/static_epistemic_access/stratum.yaml": "4c6a37e6e20d296906dff71d437411a0b0b61bc34e8880754c3ca87516a75958",
    "configs/static_epistemic_access/variables.yaml": "e653527bee2199ecad7bcb26f387060f3c6702f9f618396229c2461e81c81776",
    "configs/test/action_masking/actions.yaml": "c98d76e064dce68b4c51031904f632ac21b651eaee92f2c0d4661ce14fdd15ef",
    "configs/test/action_masking/brain.yaml": "aa3443bc7c0f1a07ce4863bd0aed84af862a8d6f00a89d76d397809b4135abe0",
    "configs/test/action_masking/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/action_masking/environment.yaml": "293ee8fd98e32c93872cf36fcf8936ec580bf5909cd1c9d411733ef0e2d10106",
    "configs/test/action_masking/experiment.yaml": "884aad07a7099b77185701b9a5e09421ec72d76e4d55def10ff244760e7b4b57",
    "configs/test/action_masking/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/action_masking/levels/L0_masking/affordances.yaml": "0ec8b30998c5bd097bc3b21da1a6cb4d28bd8e8bb6f258243eaf916ad5289d8e",
    "configs/test/action_masking/levels/L0_masking/bars.yaml": "51fdb5770fd723a3e350601f885cf44f7f9bd59d9776bca8400766e5962cf6a1",
    "configs/test/action_masking/levels/L0_masking/curriculum.yaml": "63881d3e4edca5b121d56736cf110a4bb7200082a4500ff11c631cbb9b72e0f5",
    "configs/test/action_masking/levels/L0_masking/drive.yaml": "685e0a90a17ebb9c0395fad20d65eba445af56e446efb50cbbc11b755f2e6f26",
    "configs/test/action_masking/levels/L0_masking/training.yaml": "69fd7631ad3f575143b828620bc9bd8d7d5a6d52287e88d3ce3914f5ed473f5d",
    "configs/test/action_masking/stratum.yaml": "6651321675a90b013b9de83bac3b4860621246a035665e2baf3ca56cff8d9907",
    "configs/test/action_masking/variables.yaml": "bf717444ec20cf907edaf3a24809764b6c209605445740431779379edcb0f475",
    "configs/test/action_space/aspatial/actions.yaml": "d9f4ae5d0f39422d2a2752c6b832387a522b970bb9d2fe2958e21a0fbbba6b08",
    "configs/test/action_space/aspatial/brain.yaml": "4f7c36655a55862ec600e736782df893dd530eb68d8e84e4617e392302fd4f40",
    "configs/test/action_space/aspatial/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/action_space/aspatial/environment.yaml": "f81ed6fe2b1a44a33b81ee4141c5c2d1a75149383b8e2f60115530c6a0a2c4ba",
    "configs/test/action_space/aspatial/experiment.yaml": "518589d2164be7126be79d13d7a69a5bc024f3c4c0b4a896291dce43a38416d8",
    "configs/test/action_space/aspatial/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/action_space/aspatial/levels/L0/affordances.yaml": "b76f46b120ad02c9b1249920c8770c2ddb01da9f376aa33c65a7fd53e37dfaf3",
    "configs/test/action_space/aspatial/levels/L0/bars.yaml": "c707622784d58c08d79eab895c2232a7d58b02a0fd40dbc783d728d1467e78f0",
    "configs/test/action_space/aspatial/levels/L0/curriculum.yaml": "d77d937b25d33c9c2d1cbf62c9b5a48a0e645f299fa7ccf639c11055cde502f5",
    "configs/test/action_space/aspatial/levels/L0/drive.yaml": "b07f4bc73081a12be1d0124374ee99e793188b1c341bab8302ae4ebf11442feb",
    "configs/test/action_space/aspatial/levels/L0/training.yaml": "9680798f818416d5578b1bdd0a5dcb005392726508e77614774e217a405920f2",
    "configs/test/action_space/aspatial/stratum.yaml": "291e2403a4b23262061dd4a0bae5219f0e1f3d6a60fe3d958dbfced67ed735eb",
    "configs/test/action_space/aspatial/variables.yaml": "bf717444ec20cf907edaf3a24809764b6c209605445740431779379edcb0f475",
    "configs/test/action_space/continuous1d/actions.yaml": "d9f4ae5d0f39422d2a2752c6b832387a522b970bb9d2fe2958e21a0fbbba6b08",
    "configs/test/action_space/continuous1d/brain.yaml": "7b4fa14086c78f47f4e04f769bef099269a4a1c5eccc6aba0505d47a3fd2e710",
    "configs/test/action_space/continuous1d/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/action_space/continuous1d/environment.yaml": "f81ed6fe2b1a44a33b81ee4141c5c2d1a75149383b8e2f60115530c6a0a2c4ba",
    "configs/test/action_space/continuous1d/experiment.yaml": "e6f53e18582711a9535fe311d17e41d03198bc3d4d935b38bff5f21660774770",
    "configs/test/action_space/continuous1d/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/action_space/continuous1d/levels/L0/affordances.yaml": "86a645eb600b95070cd0291bbc417dfcdde3ad4268d19125844a59b34adaf405",
    "configs/test/action_space/continuous1d/levels/L0/bars.yaml": "c707622784d58c08d79eab895c2232a7d58b02a0fd40dbc783d728d1467e78f0",
    "configs/test/action_space/continuous1d/levels/L0/curriculum.yaml": "d77d937b25d33c9c2d1cbf62c9b5a48a0e645f299fa7ccf639c11055cde502f5",
    "configs/test/action_space/continuous1d/levels/L0/drive.yaml": "b07f4bc73081a12be1d0124374ee99e793188b1c341bab8302ae4ebf11442feb",
    "configs/test/action_space/continuous1d/levels/L0/training.yaml": "2d898dd9f9ce50687f72b8bd0cb17b2e4a07ffc3b143edb7e4569ad6fb5ec483",
    "configs/test/action_space/continuous1d/stratum.yaml": "12d4047f47644bacc6a55ef70967ee9405338abde9a933cff0a3c9a79b66ab00",
    "configs/test/action_space/continuous1d/variables.yaml": "bf717444ec20cf907edaf3a24809764b6c209605445740431779379edcb0f475",
    "configs/test/action_space/grid2d/actions.yaml": "d9f4ae5d0f39422d2a2752c6b832387a522b970bb9d2fe2958e21a0fbbba6b08",
    "configs/test/action_space/grid2d/brain.yaml": "44113eda65c0796c6a9f4ab62a27ba30dddeb3ccf40283c3f9b5514a67d271e8",
    "configs/test/action_space/grid2d/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/action_space/grid2d/environment.yaml": "6e7ee15af950fc8dc3aa09827f281ce93874352cbaf5f3990824e6bcbd63db59",
    "configs/test/action_space/grid2d/experiment.yaml": "9d829778508f9899d4ab9727ca9b698eaa05d8221d04810393936711813b2572",
    "configs/test/action_space/grid2d/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/action_space/grid2d/levels/L0/affordances.yaml": "f4636cccb3b2d3ab6dbae74b5b7df454472f19b653ccec91fd39a033ad14bf0f",
    "configs/test/action_space/grid2d/levels/L0/bars.yaml": "c707622784d58c08d79eab895c2232a7d58b02a0fd40dbc783d728d1467e78f0",
    "configs/test/action_space/grid2d/levels/L0/curriculum.yaml": "d77d937b25d33c9c2d1cbf62c9b5a48a0e645f299fa7ccf639c11055cde502f5",
    "configs/test/action_space/grid2d/levels/L0/drive.yaml": "b07f4bc73081a12be1d0124374ee99e793188b1c341bab8302ae4ebf11442feb",
    "configs/test/action_space/grid2d/levels/L0/training.yaml": "088ef7e326626e3b46a102167337dc0ff62b7d4efaa2e5799943ffc5db65cecc",
    "configs/test/action_space/grid2d/stratum.yaml": "f7f88d64b676c0f3e1449b630b5e51acd32e953429cb54bf4e00668d7cc03611",
    "configs/test/action_space/grid2d/variables.yaml": "bf717444ec20cf907edaf3a24809764b6c209605445740431779379edcb0f475",
    "configs/test/effects_smoke/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/effects_smoke/brain.yaml": "190c53df401613b1fadd812033946d6c89b1cbcd7cc30bb62f5959ba710716b9",
    "configs/test/effects_smoke/effects.yaml": "fb3c76b1560ccd07fe5b7d6b909483793f1b85e21553921e62615bc3ce7b0eeb",
    "configs/test/effects_smoke/environment.yaml": "100b917a777b5efb20fbb130d7cccdb55e50e57c842ae468af05bebeab61246b",
    "configs/test/effects_smoke/experiment.yaml": "8376f7e5acfb331b265de7ce3b71f75f67e7a066f9cc818a0962768383ac1844",
    "configs/test/effects_smoke/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/effects_smoke/levels/L0_effects/affordances.yaml": "02e0bd95778c3dc31d0e83cf3ac31741239f6b2e85465fed0e75d301e5db2a40",
    "configs/test/effects_smoke/levels/L0_effects/bars.yaml": "7ee452518d4a3ad1bb0f47079ca1754fd4a11a61ff01a3295a3e14bebc9eed82",
    "configs/test/effects_smoke/levels/L0_effects/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/effects_smoke/levels/L0_effects/drive.yaml": "4c3b0c9c278c8e872de2bbc87d2a36eaa6fd545e31ae3a1f34c92df87e04eddf",
    "configs/test/effects_smoke/levels/L0_effects/training.yaml": "23c48c0ae7569b1731f0a6bdfdfd523dad8d313bb81839bf11e284effbf3a907",
    "configs/test/effects_smoke/stratum.yaml": "3d7d7c38f5879e30042d39af802e4844e935bd48f521903421199a60079ed97c",
    "configs/test/effects_smoke/variables.yaml": "fa0741458368c54016c668d2e6019666db08de3ed1cf2762f84a6e76bfd1d0c1",
    "configs/test/episode_lanes/actions.yaml": "278b4edf637c3b2e1f693215489f54ea8ffa6ffa102a42092eecf7548d93f20d",
    "configs/test/episode_lanes/brain.yaml": "45fd26add306fc29a9ea0b913172e0ed636cf14ad5117bf44b03226011ff22a5",
    "configs/test/episode_lanes/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/episode_lanes/environment.yaml": "68e02ff025dda2c82e08608632b46675c286dcc0f73a4d94b9b4c66dbbb26253",
    "configs/test/episode_lanes/experiment.yaml": "4df6c85fb5c4818136cf700d00a74556c2a1dd1dbdd781babdc5b0c6a7614c08",
    "configs/test/episode_lanes/items.yaml": "b7e8de3f8a153e7293b713ba81be3a318724d3688ac67df29bd622a302aadd26",
    "configs/test/episode_lanes/levels/L0_test/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/test/episode_lanes/levels/L0_test/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/test/episode_lanes/levels/L0_test/curriculum.yaml": "e24d6f042e667615359ff43b8c6e2c84982695bfcd6c8ed5795f48a2eb3201e8",
    "configs/test/episode_lanes/levels/L0_test/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/test/episode_lanes/levels/L0_test/training.yaml": "d08110d6412642bdfec5bce541899af5a15b2bac57a0245a2472d516ac89674d",
    "configs/test/episode_lanes/stratum.yaml": "9848f77098f4faa2d934dc8284ae37e47b33d34e6fc909187b2fb87b5c7022a8",
    "configs/test/episode_lanes/variables.yaml": "ebbd524f99816edfbfbdb9b654fe19953cee5a16871dfd485f8579fbd0d5cfee",
    "configs/test/gridnd_4d_pack/actions.yaml": "f64aedaae752d3c048b61b7b20fc4c5419858b03496ada72d479bbc58d5e591d",
    "configs/test/gridnd_4d_pack/brain.yaml": "02e781dedac51916e1bd477dc5f39fa428307dd430d68b08363471e5ea7c25de",
    "configs/test/gridnd_4d_pack/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/gridnd_4d_pack/environment.yaml": "dc902c1bcfeaa6f730e81f0b4458a6a3e2577880f7ed633a1cc4e977e2753483",
    "configs/test/gridnd_4d_pack/experiment.yaml": "24ef9fd411e78e1b1bebc80e6be3e8cfe77d80f5145b272954bfeb2069810c3c",
    "configs/test/gridnd_4d_pack/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/gridnd_4d_pack/levels/L0_test/affordances.yaml": "b76d7f07807bf1ea37d2032c9e5d66d398a29c385762a6801df562e4757ac35c",
    "configs/test/gridnd_4d_pack/levels/L0_test/bars.yaml": "c1b7c8ceb0f05f5fe702ee560dc53d037aef92dcb60bb3622fa1c2f80b18bd1f",
    "configs/test/gridnd_4d_pack/levels/L0_test/curriculum.yaml": "dc5c2428c363ddba6d22da4e3fef38744d42d72ad956b7d3f38656fc5d53604b",
    "configs/test/gridnd_4d_pack/levels/L0_test/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/test/gridnd_4d_pack/levels/L0_test/training.yaml": "10eca531d2b53f8fb70f68718d561b6fcba9c39444bfec1e8bc0c6987dc63f32",
    "configs/test/gridnd_4d_pack/stratum.yaml": "1feed23a09bc8786f02dcdcf6be0f55571de6c0b8a03e35e5b4580785dd51661",
    "configs/test/gridnd_4d_pack/variables.yaml": "55cd5ff8ac9f19ef758699d38c6402b75142b409d5cb62b712a3293df6b1ea89",
    "configs/test/items_smoke/actions.yaml": "c98d76e064dce68b4c51031904f632ac21b651eaee92f2c0d4661ce14fdd15ef",
    "configs/test/items_smoke/brain.yaml": "e0fff02ab1af345bd9dedb056c606f67d719057ced39cf143ad68c5bcf5a7627",
    "configs/test/items_smoke/effects.yaml": "0e434a1b8a1e2ca957bf0a423049a459c383e5262b35dacc4cabdb03f29e2a1a",
    "configs/test/items_smoke/environment.yaml": "8e70f439c305f2c3c2f2c9bc878a4ebcb1afbe895e900b2d12e1fb4a7b354e64",
    "configs/test/items_smoke/experiment.yaml": "2303d6e171ca8c44b58def67bae8cdc1e39a8f61b1ae69dca58f4d56c1d8a4c3",
    "configs/test/items_smoke/items.yaml": "94ddb1f4fbddf2f5f91f9e24a0ddac74b9fbd57edfb1d21b81ce1cb825612127",
    "configs/test/items_smoke/levels/L0_smoke/affordances.yaml": "a5cc1b708460b901eaef66df75487fc9ba324d2858d713b516f6a73781ef7098",
    "configs/test/items_smoke/levels/L0_smoke/bars.yaml": "040b63ba2a146cd3c762a547cae6d51243bee3a5cdf4fccecedde516d998d9d2",
    "configs/test/items_smoke/levels/L0_smoke/curriculum.yaml": "ad5461940b42f7030c7c258441ccdbc4142ba1c1da409756c3520389f47b8963",
    "configs/test/items_smoke/levels/L0_smoke/drive.yaml": "f6e177a29b05a16e43599bf8b05c42e978379925a6e813e7ae4eede2a725a396",
    "configs/test/items_smoke/levels/L0_smoke/items.yaml": "5e170612edf95c3381f4f3c0e72ddf04b5286516be44a23e1f4eae5dfe715039",
    "configs/test/items_smoke/levels/L0_smoke/training.yaml": "f947a1d0bc87f6c0fc30f5114d28402d9e4716e6ae5a21956b3beaddd5168bfb",
    "configs/test/items_smoke/stratum.yaml": "aad8b287c76fd5b1cb6f67b11934948757c854edc184f9a0a6791d3665df653e",
    "configs/test/items_smoke/variables.yaml": "cdcfd10090fda619b28c810f9dbc90ec7a2fba1f96ec56d89c08295f6033f3b4",
    "configs/test/model_config/actions.yaml": "16d5b0c73b3abeec496cc7571394b8ef8950c55a24e185ee2b4f03d9c6d36b14",
    "configs/test/model_config/brain.yaml": "45fd26add306fc29a9ea0b913172e0ed636cf14ad5117bf44b03226011ff22a5",
    "configs/test/model_config/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/model_config/environment.yaml": "68e02ff025dda2c82e08608632b46675c286dcc0f73a4d94b9b4c66dbbb26253",
    "configs/test/model_config/experiment.yaml": "e6e9c4f88578541a109c85f45e6bdb8bc82e7cbcc35380c8372a32dce8c1155d",
    "configs/test/model_config/items.yaml": "b7e8de3f8a153e7293b713ba81be3a318724d3688ac67df29bd622a302aadd26",
    "configs/test/model_config/levels/L0_test/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/test/model_config/levels/L0_test/bars.yaml": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
    "configs/test/model_config/levels/L0_test/curriculum.yaml": "e24d6f042e667615359ff43b8c6e2c84982695bfcd6c8ed5795f48a2eb3201e8",
    "configs/test/model_config/levels/L0_test/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/test/model_config/levels/L0_test/training.yaml": "65a4f11ea2cfa81717222c35c5597ffe404b58413043decafd814545ac852196",
    "configs/test/model_config/stratum.yaml": "9848f77098f4faa2d934dc8284ae37e47b33d34e6fc909187b2fb87b5c7022a8",
    "configs/test/model_config/variables.yaml": "ebbd524f99816edfbfbdb9b654fe19953cee5a16871dfd485f8579fbd0d5cfee",
    "configs/test/model_config_12meter/actions.yaml": "5f94d0b8c4b2d10beffd479b43e1d21a95d5601d46dcd034931e73f0e0cd45be",
    "configs/test/model_config_12meter/brain.yaml": "c3f65dbc6b944b7b3df0065f1ccf4cdc9517010cb80767ffb2f1275ed4f9a6ac",
    "configs/test/model_config_12meter/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/model_config_12meter/environment.yaml": "e3888ea562656c497c7aa0780efb04dce29c82bdecbb250f29ee256290ea2871",
    "configs/test/model_config_12meter/experiment.yaml": "245392fa2555cb9ada657df8c47a7adf43acad1e71b56f9e382516904caf41f9",
    "configs/test/model_config_12meter/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/model_config_12meter/levels/L0_12meter/affordances.yaml": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
    "configs/test/model_config_12meter/levels/L0_12meter/bars.yaml": "27de67287bb7de4e9bbf45900f24aed7d453f821cad1c4cf4c452760e64867ce",
    "configs/test/model_config_12meter/levels/L0_12meter/curriculum.yaml": "fc41e113e7ca1d9a588a608a431fb6a6bb0cc02f422faad927201a6164b72243",
    "configs/test/model_config_12meter/levels/L0_12meter/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/test/model_config_12meter/levels/L0_12meter/training.yaml": "e8017cbf47b844653c2fe9b52f1b135b3126dc18d01aee0a2837a03a548d0206",
    "configs/test/model_config_12meter/stratum.yaml": "b0af3317051c7e71fb14b70b1b4f8abbf13f38a9b9776999d776f29a35ef7609",
    "configs/test/model_config_12meter/variables.yaml": "8e7830a1c9cb0e56037b97e4899e5f3c1ede4d69f3351d9adc7b6157c1d56a72",
    "configs/test/model_config_4meter/actions.yaml": "5f94d0b8c4b2d10beffd479b43e1d21a95d5601d46dcd034931e73f0e0cd45be",
    "configs/test/model_config_4meter/brain.yaml": "d3cb675dfd3c7067e3bd68a78b907a432fd3f35d7f63743a73a054ce30ef756c",
    "configs/test/model_config_4meter/effects.yaml": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
    "configs/test/model_config_4meter/environment.yaml": "885ece5f101606954d2a63cd71d3c5efd7363f94ddb29697e2a5089733c12bbd",
    "configs/test/model_config_4meter/experiment.yaml": "a3187bbe565c1ff1eebde721188b9109240b42f5652bfd7c80d600695bb17426",
    "configs/test/model_config_4meter/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/model_config_4meter/levels/L0_4meter/affordances.yaml": "0efb9bff7bd5178c61b24e3c0a6a480f64dc4106fcf362dd37c57b8fbc8ab9f8",
    "configs/test/model_config_4meter/levels/L0_4meter/bars.yaml": "55c9221a7007772e818c8e89cdeee9c7532ee444762473707d15eea33ebe08ab",
    "configs/test/model_config_4meter/levels/L0_4meter/curriculum.yaml": "fc41e113e7ca1d9a588a608a431fb6a6bb0cc02f422faad927201a6164b72243",
    "configs/test/model_config_4meter/levels/L0_4meter/drive.yaml": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
    "configs/test/model_config_4meter/levels/L0_4meter/training.yaml": "e8017cbf47b844653c2fe9b52f1b135b3126dc18d01aee0a2837a03a548d0206",
    "configs/test/model_config_4meter/stratum.yaml": "b0af3317051c7e71fb14b70b1b4f8abbf13f38a9b9776999d776f29a35ef7609",
    "configs/test/model_config_4meter/variables.yaml": "d6d9af81724eca7cc78c86d098da8f7fd087528e058135f31d8e0db0974f42ab",
    "configs/test/token_set_smoke/actions.yaml": "7363114f30b2794659da1ec49aef65b5800c0addf5be659997c5e103d4180653",
    "configs/test/token_set_smoke/brain.yaml": "9629e1b27c3bb8931cec870a53ae760760e2cdf90158cb5862ce1a3ad5928979",
    "configs/test/token_set_smoke/effects.yaml": "2b9f559e318f638d2d96a8c5d5efd45a8bd9f22b739b6625053e0c2d8e737fa9",
    "configs/test/token_set_smoke/environment.yaml": "400cf6c4f32ea05355704f1a1e8bd4d46bd2e2fed8be9f370123e518e4d7f9d0",
    "configs/test/token_set_smoke/experiment.yaml": "69931d8a790795f39ceea47d91df013983cd838ca7892b8f61ec8542361a727c",
    "configs/test/token_set_smoke/items.yaml": "5121217232857b0e3551f484dcaa32a82d0e104e3e74a3316ac8183b9beb818e",
    "configs/test/token_set_smoke/levels/L0_test/affordances.yaml": "5157d88e7191296d671aaf6e002c94786af3ba0cf9de46259ad323a261b78009",
    "configs/test/token_set_smoke/levels/L0_test/bars.yaml": "c050412a304078501fe2f1ff2da41cf5bdee632aa1ef500948c04b90a9d8814b",
    "configs/test/token_set_smoke/levels/L0_test/curriculum.yaml": "3cc1e1583939f8d1fd4b6be265250ec174fea6ceb24712150892b7d64599b987",
    "configs/test/token_set_smoke/levels/L0_test/drive.yaml": "b4ec89fb5e214e40e7f6c8c1f9d60301dc6bac92062ccad89fa20cf6b445f937",
    "configs/test/token_set_smoke/levels/L0_test/training.yaml": "318d7304a2f9e9bfc76a7c86257968ee2064bbc3e08d644ab5f54300a8084165",
    "configs/test/token_set_smoke/levels/L1_attention/affordances.yaml": "5157d88e7191296d671aaf6e002c94786af3ba0cf9de46259ad323a261b78009",
    "configs/test/token_set_smoke/levels/L1_attention/bars.yaml": "c050412a304078501fe2f1ff2da41cf5bdee632aa1ef500948c04b90a9d8814b",
    "configs/test/token_set_smoke/levels/L1_attention/brain.yaml": "60e014d4d9883c4acb098d9695863417527a09f2f79c98a9271e0b5798173c3e",
    "configs/test/token_set_smoke/levels/L1_attention/curriculum.yaml": "3cc1e1583939f8d1fd4b6be265250ec174fea6ceb24712150892b7d64599b987",
    "configs/test/token_set_smoke/levels/L1_attention/drive.yaml": "b4ec89fb5e214e40e7f6c8c1f9d60301dc6bac92062ccad89fa20cf6b445f937",
    "configs/test/token_set_smoke/levels/L1_attention/training.yaml": "318d7304a2f9e9bfc76a7c86257968ee2064bbc3e08d644ab5f54300a8084165",
    "configs/test/token_set_smoke/stratum.yaml": "d78508ca7d6b3a72966a766829e75e9deefff9300f21bfd4e801a7769dcb26d2",
    "configs/test/token_set_smoke/variables.yaml": "5529bf50ab035dd5b6052d6da614bfd6f968842de35ee1317eeed4f8d6cbde4c",
    "configs/test/token_transfer_a/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/token_transfer_a/brain.yaml": "b5b288d68c997b157402285f2a5a0c259175d28cec976618f1b28a8677b22285",
    "configs/test/token_transfer_a/environment.yaml": "8cdf6c78da7e0be46e413bdef0ff31a0dec077ebd4ea4dde205fb6acab603d6c",
    "configs/test/token_transfer_a/experiment.yaml": "59c12cc2f5c2c6ee50adcc9182db12faae0b61f2657b9d9363731771dbb0c22f",
    "configs/test/token_transfer_a/items.yaml": "b7e8de3f8a153e7293b713ba81be3a318724d3688ac67df29bd622a302aadd26",
    "configs/test/token_transfer_a/levels/L0_transfer/affordances.yaml": "02e0bd95778c3dc31d0e83cf3ac31741239f6b2e85465fed0e75d301e5db2a40",
    "configs/test/token_transfer_a/levels/L0_transfer/bars.yaml": "7ee452518d4a3ad1bb0f47079ca1754fd4a11a61ff01a3295a3e14bebc9eed82",
    "configs/test/token_transfer_a/levels/L0_transfer/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/token_transfer_a/levels/L0_transfer/drive.yaml": "4c3b0c9c278c8e872de2bbc87d2a36eaa6fd545e31ae3a1f34c92df87e04eddf",
    "configs/test/token_transfer_a/levels/L0_transfer/training.yaml": "23c48c0ae7569b1731f0a6bdfdfd523dad8d313bb81839bf11e284effbf3a907",
    "configs/test/token_transfer_a/stratum.yaml": "3d7d7c38f5879e30042d39af802e4844e935bd48f521903421199a60079ed97c",
    "configs/test/token_transfer_a/variables.yaml": "8875dc3b33d39641c12effc6ddc0c2f2137cf6dc834e2fdd124930ac7b114476",
    "configs/test/token_transfer_b/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/token_transfer_b/brain.yaml": "b5b288d68c997b157402285f2a5a0c259175d28cec976618f1b28a8677b22285",
    "configs/test/token_transfer_b/environment.yaml": "100b917a777b5efb20fbb130d7cccdb55e50e57c842ae468af05bebeab61246b",
    "configs/test/token_transfer_b/experiment.yaml": "eb277e4fe3ac6359da3c09a6b54629da8ad1e164141552a8455153fbce3f3d4c",
    "configs/test/token_transfer_b/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/token_transfer_b/levels/L0_transfer/affordances.yaml": "02e0bd95778c3dc31d0e83cf3ac31741239f6b2e85465fed0e75d301e5db2a40",
    "configs/test/token_transfer_b/levels/L0_transfer/bars.yaml": "7ee452518d4a3ad1bb0f47079ca1754fd4a11a61ff01a3295a3e14bebc9eed82",
    "configs/test/token_transfer_b/levels/L0_transfer/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/token_transfer_b/levels/L0_transfer/drive.yaml": "4c3b0c9c278c8e872de2bbc87d2a36eaa6fd545e31ae3a1f34c92df87e04eddf",
    "configs/test/token_transfer_b/levels/L0_transfer/training.yaml": "23c48c0ae7569b1731f0a6bdfdfd523dad8d313bb81839bf11e284effbf3a907",
    "configs/test/token_transfer_b/stratum.yaml": "3d7d7c38f5879e30042d39af802e4844e935bd48f521903421199a60079ed97c",
    "configs/test/token_transfer_b/variables.yaml": "bf717444ec20cf907edaf3a24809764b6c209605445740431779379edcb0f475",
    "configs/test/token_transfer_c/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/token_transfer_c/brain.yaml": "b5b288d68c997b157402285f2a5a0c259175d28cec976618f1b28a8677b22285",
    "configs/test/token_transfer_c/environment.yaml": "100b917a777b5efb20fbb130d7cccdb55e50e57c842ae468af05bebeab61246b",
    "configs/test/token_transfer_c/experiment.yaml": "7b64407350c887cf5dfa317356b0bea936abe19151c567bcedc677072a720e2e",
    "configs/test/token_transfer_c/items.yaml": "b7e8de3f8a153e7293b713ba81be3a318724d3688ac67df29bd622a302aadd26",
    "configs/test/token_transfer_c/levels/L0_transfer/affordances.yaml": "02e0bd95778c3dc31d0e83cf3ac31741239f6b2e85465fed0e75d301e5db2a40",
    "configs/test/token_transfer_c/levels/L0_transfer/bars.yaml": "7ee452518d4a3ad1bb0f47079ca1754fd4a11a61ff01a3295a3e14bebc9eed82",
    "configs/test/token_transfer_c/levels/L0_transfer/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/token_transfer_c/levels/L0_transfer/drive.yaml": "4c3b0c9c278c8e872de2bbc87d2a36eaa6fd545e31ae3a1f34c92df87e04eddf",
    "configs/test/token_transfer_c/levels/L0_transfer/training.yaml": "23c48c0ae7569b1731f0a6bdfdfd523dad8d313bb81839bf11e284effbf3a907",
    "configs/test/token_transfer_c/stratum.yaml": "3d7d7c38f5879e30042d39af802e4844e935bd48f521903421199a60079ed97c",
    "configs/test/token_transfer_c/variables.yaml": "bf717444ec20cf907edaf3a24809764b6c209605445740431779379edcb0f475",
    "configs/test/vfs_bar_access/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/vfs_bar_access/brain.yaml": "3fa52599ca4d0b89a9610795af217cb62706b1dc95e5ef349898b115ef2c3b53",
    "configs/test/vfs_bar_access/effects.yaml": "6ddf5aa0c8d6a47bf94123bd9e8c7c08dc31990f67281d2487467a52d06bddff",
    "configs/test/vfs_bar_access/environment.yaml": "80800986e3f31a9e9fdbb9ca63376b6844a7200d7f76d46d0deaac75eb76d7c0",
    "configs/test/vfs_bar_access/experiment.yaml": "4317043db7c47a104b13f22662d48491bbbc9e3921d922ad6d5f125f02b452a0",
    "configs/test/vfs_bar_access/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/vfs_bar_access/levels/L0_bars/affordances.yaml": "87f6b0b6ea83ee5f52ea16839a4d9238df3b7279b852bb5ad629d1fafc137d3b",
    "configs/test/vfs_bar_access/levels/L0_bars/bars.yaml": "c44a003903ed0ed4bfa5bb12a06eea47a8fb87e8d2ea1913a8bf2d870cbd24b6",
    "configs/test/vfs_bar_access/levels/L0_bars/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/vfs_bar_access/levels/L0_bars/drive.yaml": "1caaae86357da011565d132e33a6d16a04204f8d82b9e554ed12f4935edaca6a",
    "configs/test/vfs_bar_access/levels/L0_bars/training.yaml": "bff32f1705f48cf1c356b173d1e896ce42ec9dadee93572bd64303cfcd759481",
    "configs/test/vfs_bar_access/stratum.yaml": "086b4d9c11f2a6e75b8fc20682d76d4ab8e9b1fe89cdca05c6aaf7ae3591eaf3",
    "configs/test/vfs_bar_access/variables.yaml": "f7cb68c285cef1b01565293d1ca69defe6688794badcbb48a190da9daa01a881",
    "configs/test/vfs_circular_dependency/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/vfs_circular_dependency/brain.yaml": "6e6b7bfa2e6809c5ccf4fad32d2ac06cbf180ba81c2aa7b7f8697cf1976cd846",
    "configs/test/vfs_circular_dependency/environment.yaml": "80800986e3f31a9e9fdbb9ca63376b6844a7200d7f76d46d0deaac75eb76d7c0",
    "configs/test/vfs_circular_dependency/experiment.yaml": "895d168b9583477116b67fb81cb7b7ffe53b3e2415e65a9deefb1b6f14c7c529",
    "configs/test/vfs_circular_dependency/items.yaml": "19e03e891f02d1a3c2062699861e5493c5fdf154a3e9afb52a4e88d3edd5d35c",
    "configs/test/vfs_circular_dependency/levels/L0_circular/affordances.yaml": "87f6b0b6ea83ee5f52ea16839a4d9238df3b7279b852bb5ad629d1fafc137d3b",
    "configs/test/vfs_circular_dependency/levels/L0_circular/bars.yaml": "c44a003903ed0ed4bfa5bb12a06eea47a8fb87e8d2ea1913a8bf2d870cbd24b6",
    "configs/test/vfs_circular_dependency/levels/L0_circular/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/vfs_circular_dependency/levels/L0_circular/drive.yaml": "1caaae86357da011565d132e33a6d16a04204f8d82b9e554ed12f4935edaca6a",
    "configs/test/vfs_circular_dependency/levels/L0_circular/training.yaml": "bff32f1705f48cf1c356b173d1e896ce42ec9dadee93572bd64303cfcd759481",
    "configs/test/vfs_circular_dependency/stratum.yaml": "086b4d9c11f2a6e75b8fc20682d76d4ab8e9b1fe89cdca05c6aaf7ae3591eaf3",
    "configs/test/vfs_circular_dependency/variables.yaml": "21ffca5396a61f2209e27de04ec80ff6d9a3873f03bb79677f356b7fc2982352",
    "configs/test/vfs_dependency_chain/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/vfs_dependency_chain/brain.yaml": "33a9ba05954ea172ae81e853e4f9579434972b8ff75642bef4f9207b52bb19fa",
    "configs/test/vfs_dependency_chain/effects.yaml": "6ddf5aa0c8d6a47bf94123bd9e8c7c08dc31990f67281d2487467a52d06bddff",
    "configs/test/vfs_dependency_chain/environment.yaml": "80800986e3f31a9e9fdbb9ca63376b6844a7200d7f76d46d0deaac75eb76d7c0",
    "configs/test/vfs_dependency_chain/experiment.yaml": "f07dcdab786ba5bf2a26920af1cb1961c62f7623c9f650931b138594c84d299e",
    "configs/test/vfs_dependency_chain/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/vfs_dependency_chain/levels/L0_deps/affordances.yaml": "87f6b0b6ea83ee5f52ea16839a4d9238df3b7279b852bb5ad629d1fafc137d3b",
    "configs/test/vfs_dependency_chain/levels/L0_deps/bars.yaml": "c44a003903ed0ed4bfa5bb12a06eea47a8fb87e8d2ea1913a8bf2d870cbd24b6",
    "configs/test/vfs_dependency_chain/levels/L0_deps/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/vfs_dependency_chain/levels/L0_deps/drive.yaml": "1caaae86357da011565d132e33a6d16a04204f8d82b9e554ed12f4935edaca6a",
    "configs/test/vfs_dependency_chain/levels/L0_deps/training.yaml": "bff32f1705f48cf1c356b173d1e896ce42ec9dadee93572bd64303cfcd759481",
    "configs/test/vfs_dependency_chain/stratum.yaml": "086b4d9c11f2a6e75b8fc20682d76d4ab8e9b1fe89cdca05c6aaf7ae3591eaf3",
    "configs/test/vfs_dependency_chain/variables.yaml": "3be1fecf36fe84c877401640c5c42d3f6b6db3c4b6f6d1679c7481c4e9b3afb9",
    "configs/test/vfs_profiles_smoke/variables.yaml": "eb6fa8083e848091810e0000d518e41000716364c9525524f1f9c5acaa24306a",
    "configs/test/vfs_type_mismatch/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/vfs_type_mismatch/brain.yaml": "b23f0ed467954a38007729b8caa9d2a60456bd207ab98b7251c0a815158a10be",
    "configs/test/vfs_type_mismatch/effects.yaml": "32db7eda6b6d807cc6ff9e6feb05f2e2476da31634d6b1ac7a8f563c0f3e6396",
    "configs/test/vfs_type_mismatch/environment.yaml": "80800986e3f31a9e9fdbb9ca63376b6844a7200d7f76d46d0deaac75eb76d7c0",
    "configs/test/vfs_type_mismatch/experiment.yaml": "41dc29161f4fef94909ada14e3b60dfb20772dfd82dade1cea7158ebf4fefb2c",
    "configs/test/vfs_type_mismatch/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/vfs_type_mismatch/levels/L0_type_mismatch/affordances.yaml": "87f6b0b6ea83ee5f52ea16839a4d9238df3b7279b852bb5ad629d1fafc137d3b",
    "configs/test/vfs_type_mismatch/levels/L0_type_mismatch/bars.yaml": "c44a003903ed0ed4bfa5bb12a06eea47a8fb87e8d2ea1913a8bf2d870cbd24b6",
    "configs/test/vfs_type_mismatch/levels/L0_type_mismatch/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/vfs_type_mismatch/levels/L0_type_mismatch/drive.yaml": "1caaae86357da011565d132e33a6d16a04204f8d82b9e554ed12f4935edaca6a",
    "configs/test/vfs_type_mismatch/levels/L0_type_mismatch/training.yaml": "bff32f1705f48cf1c356b173d1e896ce42ec9dadee93572bd64303cfcd759481",
    "configs/test/vfs_type_mismatch/stratum.yaml": "086b4d9c11f2a6e75b8fc20682d76d4ab8e9b1fe89cdca05c6aaf7ae3591eaf3",
    "configs/test/vfs_type_mismatch/variables.yaml": "cd363314a1fac80a82b59318bb55ab95ca865d75c1c5eaa3241eb06ddfe4e351",
    "configs/test/vfs_undefined_var/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/test/vfs_undefined_var/brain.yaml": "34e9e7199f2592428aa11f4fdd06d3ac6be5bbb2cbb793a6c4608b834624f544",
    "configs/test/vfs_undefined_var/effects.yaml": "32db7eda6b6d807cc6ff9e6feb05f2e2476da31634d6b1ac7a8f563c0f3e6396",
    "configs/test/vfs_undefined_var/environment.yaml": "80800986e3f31a9e9fdbb9ca63376b6844a7200d7f76d46d0deaac75eb76d7c0",
    "configs/test/vfs_undefined_var/experiment.yaml": "bfe315a4c1d436b8571e07b794e34bb8e5aa084e9afc329d8801e3f13578cec4",
    "configs/test/vfs_undefined_var/items.yaml": "074f34266cf8a9c60d0760e2fa8ba6c6d73d85d3ea19c45699b504abc053c3d5",
    "configs/test/vfs_undefined_var/levels/L0_undefined/affordances.yaml": "87f6b0b6ea83ee5f52ea16839a4d9238df3b7279b852bb5ad629d1fafc137d3b",
    "configs/test/vfs_undefined_var/levels/L0_undefined/bars.yaml": "c44a003903ed0ed4bfa5bb12a06eea47a8fb87e8d2ea1913a8bf2d870cbd24b6",
    "configs/test/vfs_undefined_var/levels/L0_undefined/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/test/vfs_undefined_var/levels/L0_undefined/drive.yaml": "1caaae86357da011565d132e33a6d16a04204f8d82b9e554ed12f4935edaca6a",
    "configs/test/vfs_undefined_var/levels/L0_undefined/training.yaml": "bff32f1705f48cf1c356b173d1e896ce42ec9dadee93572bd64303cfcd759481",
    "configs/test/vfs_undefined_var/stratum.yaml": "086b4d9c11f2a6e75b8fc20682d76d4ab8e9b1fe89cdca05c6aaf7ae3591eaf3",
    "configs/test/vfs_undefined_var/variables.yaml": "0a0ee087cdb8c22fa4fec52767ddad22fd8c0d40f01551e13cfd97859d93f97d",
    "configs/trial002_money_log_gdp/actions.yaml": "c98d76e064dce68b4c51031904f632ac21b651eaee92f2c0d4661ce14fdd15ef",
    "configs/trial002_money_log_gdp/brain.yaml": "ce058bee6d948b1fe2785d8f756e7630b04d7cf18abd3b7508f7ad2fe3a75fd1",
    "configs/trial002_money_log_gdp/effects.yaml": "6c1889ee3b18d6024388a6b126e67a276addffc5c59589735584d30dfca1d00b",
    "configs/trial002_money_log_gdp/environment.yaml": "48dbd140aa34b8098a9eff5028309f0c8c7520843b767d71712d6e6603f9634c",
    "configs/trial002_money_log_gdp/experiment.yaml": "744b1e6be9bb9a12e818d57c1e473c5b9d7de9ddac9c292ce480f0591e1d6b9e",
    "configs/trial002_money_log_gdp/items.yaml": "672b1199f237dd05bc25f8d4540df7e4f037bbfbb060af1a6e5a344228347166",
    "configs/trial002_money_log_gdp/levels/L0_simple/affordances.yaml": "5664e42546cd158b852b66cc64715158594d5288ae112d0ea5f7bdf648f6d9ca",
    "configs/trial002_money_log_gdp/levels/L0_simple/bars.yaml": "bb4244a4ba2b68707b74c22b6a7e61867df564de6aa628d78ffe9d22c176f898",
    "configs/trial002_money_log_gdp/levels/L0_simple/curriculum.yaml": "82711da489a90390ce557d5c04e133b473adca93c58e78e6785ec45243293075",
    "configs/trial002_money_log_gdp/levels/L0_simple/drive.yaml": "b139146a9e6ae743893ad835ff4d9b0ee1b2971a9d7f4d246f3cc50fbd154136",
    "configs/trial002_money_log_gdp/levels/L0_simple/training.yaml": "66ba12c770d99c1a79164b628e2c081d32ea939f843e8a35306455260cab3f98",
    "configs/trial002_money_log_gdp/stratum.yaml": "4c6a37e6e20d296906dff71d437411a0b0b61bc34e8880754c3ca87516a75958",
    "configs/trial002_money_log_gdp/variables.yaml": "373b372f5c3211944aeef4e43adb046e3b483cfbf92e217e32effc33fdfe7c90",
    "configs/trial_k_cold/actions.yaml": "0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93",
    "configs/trial_k_cold/brain.yaml": "190c53df401613b1fadd812033946d6c89b1cbcd7cc30bb62f5959ba710716b9",
    "configs/trial_k_cold/effects.yaml": "1967053d48da7c9c5e151f146d742e8d73ea378f586c578609f41b9d75ee82d0",
    "configs/trial_k_cold/environment.yaml": "14d67e7cfb3db0ca15d2df5b1851c21439d85a5e73787dca139e27108c81da36",
    "configs/trial_k_cold/experiment.yaml": "3a4dc32d8e518b91a193f8d29384b23c4a7d583f4c67fe57829089ee7c7520ed",
    "configs/trial_k_cold/items.yaml": "92304dd1d049a9cdaf35065befd6bf811aebbbd1708473bf910a7be99e3d945f",
    "configs/trial_k_cold/levels/L0_cold/affordances.yaml": "44d51e4d674ff95bb2a37c0417d8633be3647c8f98e7aa608c0d4c19e3cd2e74",
    "configs/trial_k_cold/levels/L0_cold/bars.yaml": "542a96095d772c3d94900ed9cfb41a689e1b2431fb94d48ce835c3fa940402b6",
    "configs/trial_k_cold/levels/L0_cold/curriculum.yaml": "d48203cf3e965184e46be319a97c9babe815311f7efc41939682f6837bb3f4ad",
    "configs/trial_k_cold/levels/L0_cold/drive.yaml": "16c4b27f99fc2a79ce67281f6fbc8397cba221643651516482e8a6f38af2985a",
    "configs/trial_k_cold/levels/L0_cold/items.yaml": "a0e603ddccd31d963dace86f2c96b01d029f72d3c557b4059c33d780f7aa93c0",
    "configs/trial_k_cold/levels/L0_cold/training.yaml": "a362d647e4b526614f094b2e121328de8342911d5e65084421ce5c09eec964ef",
    "configs/trial_k_cold/stratum.yaml": "2ceda01b33f8472f72537cb7f1d5682eecdfdfec1c4f63ddfbe703ca7ce02c17",
    "configs/trial_k_cold/variables.yaml": "f1b9a9bbccd49cc87758cb11f31d268ae9e123a776846a3107c0eb37477d1f1f"
  },
  "new_authored_config_changes": [
    {
      "after": "278b4edf637c3b2e1f693215489f54ea8ffa6ffa102a42092eecf7548d93f20d",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/actions.yaml"
    },
    {
      "after": "45fd26add306fc29a9ea0b913172e0ed636cf14ad5117bf44b03226011ff22a5",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/brain.yaml"
    },
    {
      "after": "dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/effects.yaml"
    },
    {
      "after": "68e02ff025dda2c82e08608632b46675c286dcc0f73a4d94b9b4c66dbbb26253",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/environment.yaml"
    },
    {
      "after": "4df6c85fb5c4818136cf700d00a74556c2a1dd1dbdd781babdc5b0c6a7614c08",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/experiment.yaml"
    },
    {
      "after": "b7e8de3f8a153e7293b713ba81be3a318724d3688ac67df29bd622a302aadd26",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/items.yaml"
    },
    {
      "after": "a752e832eb7997c10ea1ecd617445ca7f9f8c82f14713cab6120068154fc2c9b",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/levels/L0_test/affordances.yaml"
    },
    {
      "after": "c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/levels/L0_test/bars.yaml"
    },
    {
      "after": "e24d6f042e667615359ff43b8c6e2c84982695bfcd6c8ed5795f48a2eb3201e8",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/levels/L0_test/curriculum.yaml"
    },
    {
      "after": "1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/levels/L0_test/drive.yaml"
    },
    {
      "after": "d08110d6412642bdfec5bce541899af5a15b2bac57a0245a2472d516ac89674d",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/levels/L0_test/training.yaml"
    },
    {
      "after": "9848f77098f4faa2d934dc8284ae37e47b33d34e6fc909187b2fb87b5c7022a8",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/stratum.yaml"
    },
    {
      "after": "ebbd524f99816edfbfbdb9b654fe19953cee5a16871dfd485f8579fbd0d5cfee",
      "after_present": true,
      "before_present": false,
      "path": "/configs/test/episode_lanes/variables.yaml"
    }
  ],
  "artifact_sha256": {
    "runs/differential/20261002-090009/boundary_wrap_L1_full_observability_cpu_seed42.actions.npz": "bc13b6feded7fd75dfb1cee6810cad23103815117ac60ffcfbff3c41c245135d",
    "runs/differential/20261002-090009/boundary_wrap_L1_full_observability_cpu_seed42.new.npz": "90a4f01f053c5c2839270b7fb1061199f3d6cd5dc849ab55be23d4702457c8b6",
    "runs/differential/20261002-090009/boundary_wrap_L1_full_observability_cpu_seed42.old.npz": "15de20a568291fa9aeabfe8488f53953b80464958944fea79151a5c1ed9b5a32",
    "runs/differential/20261002-090009/default_curriculum_L0_0_minimal_cpu_seed42.actions.npz": "bc13b6feded7fd75dfb1cee6810cad23103815117ac60ffcfbff3c41c245135d",
    "runs/differential/20261002-090009/default_curriculum_L0_0_minimal_cpu_seed42.new.npz": "aff2d046d0153be6fb8763ecc2820d861db2982ad6977690bf583a436b0a9314",
    "runs/differential/20261002-090009/default_curriculum_L0_0_minimal_cpu_seed42.old.npz": "75d02eec6b3d207c0e7ceebc87bdea7393e7612339fe53369adf0e1d0c966600",
    "runs/differential/20261002-090009/default_curriculum_L0_5_dual_resource_cpu_seed42.actions.npz": "bc13b6feded7fd75dfb1cee6810cad23103815117ac60ffcfbff3c41c245135d",
    "runs/differential/20261002-090009/default_curriculum_L0_5_dual_resource_cpu_seed42.new.npz": "1a4597d2bf2e8689e64b68596f9ec6155878e37733867e80eb37001c4fcc5b13",
    "runs/differential/20261002-090009/default_curriculum_L0_5_dual_resource_cpu_seed42.old.npz": "f0a278236ecb80bf0e409fb6e88e5572d543bd91522e7c7fc5b65020f460fb2e",
    "runs/differential/20261002-090009/default_curriculum_L1_full_observability_cpu_seed42.actions.npz": "bc13b6feded7fd75dfb1cee6810cad23103815117ac60ffcfbff3c41c245135d",
    "runs/differential/20261002-090009/default_curriculum_L1_full_observability_cpu_seed42.new.npz": "157658bdac731bc1011b5e6345181dc2cba3804207c8ec1dbf1da44294e78fec",
    "runs/differential/20261002-090009/default_curriculum_L1_full_observability_cpu_seed42.old.npz": "8e710795c6860f9a942e7b1fe7e471114d795a6d0deb216d1cf398114b70e774",
    "runs/differential/20261002-090009/default_curriculum_L2_partial_observability_cpu_seed42.actions.npz": "bc13b6feded7fd75dfb1cee6810cad23103815117ac60ffcfbff3c41c245135d",
    "runs/differential/20261002-090009/default_curriculum_L2_partial_observability_cpu_seed42.new.npz": "f46dd45ed944779847d122ab84b1df7c89fab9b1a8303cfc52e10f317c750001",
    "runs/differential/20261002-090009/default_curriculum_L2_partial_observability_cpu_seed42.old.npz": "487cb4119946c0ada30433f9c7dff1ae530b8bf1554955cc393aec7b8cc3d657",
    "runs/differential/20261002-090009/default_curriculum_L3_temporal_mechanics_cpu_seed42.actions.npz": "bc13b6feded7fd75dfb1cee6810cad23103815117ac60ffcfbff3c41c245135d",
    "runs/differential/20261002-090009/default_curriculum_L3_temporal_mechanics_cpu_seed42.new.npz": "b0c3e7b852ecaf68ab3bcf80d4c5a7bf95305cde7802e1b3976afadab91079da",
    "runs/differential/20261002-090009/default_curriculum_L3_temporal_mechanics_cpu_seed42.old.npz": "8c7f9037b416048915c8a3743ef9d8723aa83dc2af3853287202b4e61f6b33f7",
    "runs/differential/20261002-090009/div003_cubic_partial_L2_partial_observability_cpu_seed42.actions.npz": "22c869bf1b2ad8ba75c97f9b4458ab3d27e4f628cad057c94646374ed5fdcf07",
    "runs/differential/20261002-090009/div003_cubic_partial_L2_partial_observability_cpu_seed42.new.npz": "987d8acd9bd6df3e9fd0c7bcc774aece6b1ea775b05dba43a77353e11c9a7bcf",
    "runs/differential/20261002-090009/div003_cubic_partial_L2_partial_observability_cpu_seed42.old.npz": "3bd4cec03853d98dc8b5cd9f296ee40f28e8636142067e238a2bf194c7e78ff8",
    "runs/differential/20261002-090009/div003_rect_L1_full_observability_cpu_seed42.actions.npz": "fb42abc18060c65decb166c1e694a8687e0a304691bae7449866158f64d644bd",
    "runs/differential/20261002-090009/div003_rect_L1_full_observability_cpu_seed42.new.npz": "602573e667b854c1324f5d33393ec6b5f5394f47520a43c44a345c5fbfe317a5",
    "runs/differential/20261002-090009/div003_rect_L1_full_observability_cpu_seed42.old.npz": "d503d79773f0a4da697fdecba8e5a23940e74b0790a22a0ca79d6f47a0ca2055",
    "runs/differential/20261002-090009/effects_smoke_L0_effects_cpu_seed42.actions.npz": "08a9081b3210dd5582c681bfe33900515aeb9214842b16c106b98dfa6f022d3c",
    "runs/differential/20261002-090009/effects_smoke_L0_effects_cpu_seed42.new.npz": "8e4aab73f88ebde37f658cd66dfe9d142419c7105058b77339c38ae70507a0ca",
    "runs/differential/20261002-090009/effects_smoke_L0_effects_cpu_seed42.old.npz": "ef29a299816e7126989cf6abd8079c200feb10fa2956b6915ba73b0f74b49f7b",
    "runs/differential/20261002-090009/items_smoke_L0_smoke_cpu_seed42.actions.npz": "46df0eb46c42a85e14f209069e84205ecb44eaa2be7b7346a87098ef4de01f10",
    "runs/differential/20261002-090009/items_smoke_L0_smoke_cpu_seed42.new.npz": "3f1f07ae2bd36e153bb0deeeb682315bc8e970c8a8af13c0d65718366c49172c",
    "runs/differential/20261002-090009/items_smoke_L0_smoke_cpu_seed42.old.npz": "8a921c9012809d33b910c5fd49920023e8b019f39d921ab83e55f7ad9315ad1f",
    "runs/differential/20261002-090009/report.json": "033734db94902c8878b0f05bde0454b1ed7cd897a5deb35842ecc81b1541963a",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/after-census.json": "78f411ba75a6f7dd3b236f5b41166b09ac8fe034967b42d99e50e313103bdd9c",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/after-inputs.json": "e8a736798514e21a7457b2bed635a46d442a5d226b3377fe1198bdf29a12075b",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/after-resets.json": "9e02199a56f0613b55153c5ebddfbf39495d33a91eb35bc60b1c2fef32b80c24",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/after-traces.json": "8890ee4d303f1e443239ac3c853d9361a9c2b86432604947f5e8469a9bee759f",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-00.npz": "aff2d046d0153be6fb8763ecc2820d861db2982ad6977690bf583a436b0a9314",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-01.npz": "1a4597d2bf2e8689e64b68596f9ec6155878e37733867e80eb37001c4fcc5b13",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-02.npz": "157658bdac731bc1011b5e6345181dc2cba3804207c8ec1dbf1da44294e78fec",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-03.npz": "f46dd45ed944779847d122ab84b1df7c89fab9b1a8303cfc52e10f317c750001",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-04.npz": "b0c3e7b852ecaf68ab3bcf80d4c5a7bf95305cde7802e1b3976afadab91079da",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-05.npz": "90a4f01f053c5c2839270b7fb1061199f3d6cd5dc849ab55be23d4702457c8b6",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-06.npz": "987d8acd9bd6df3e9fd0c7bcc774aece6b1ea775b05dba43a77353e11c9a7bcf",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-07.npz": "602573e667b854c1324f5d33393ec6b5f5394f47520a43c44a345c5fbfe317a5",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-08.npz": "3f1f07ae2bd36e153bb0deeeb682315bc8e970c8a8af13c0d65718366c49172c",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/cpu-09.npz": "8e4aab73f88ebde37f658cd66dfe9d142419c7105058b77339c38ae70507a0ca",
    "runs/episode-lanes/2026-10-02/implementation/candidate/static-access/report.json": "4d422f6673b9fb16cca5c76987364c1f4642ec0951fee59d535caf94a14a0bea",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-08-collector.stdout": "51610079de36fa9bd3742218e8b692692645274b0d21c02256928c3366b684f3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-08-driver.npz": "bfdf146f67fe9a091072c3e32e8032f592a5b14b6d3aab5eaa4981de590ed6e4",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-08-ledger.json": "e4b236ae1baeec67945d991d346f432531bb25cd582b37296ee8dd708345f2b2",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-08-ledger.npz": "ac692435497a36c5a7dfae1821fa52220bf03d3cbca9f73f2ebdb52e42e4b6db",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-09-collector.stdout": "47c7bc79b4a68cfd216ed5c37c5d833d20aa645b8e4011f82212145a9538fbab",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-09-driver.npz": "656548e602f3ceeaab604fed5800e207b09c6f3a72cde088c83d436d85a50b03",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-09-ledger.json": "3910e3dbb7814d5f50213c3265f1ab25552b981acdc8a0ac981d94bd8d3bdab2",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E2/cpu-09-ledger.npz": "02918a717339f10d4de9e515886e6c2908cf0e706d655da927570860d384511a",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-08-collector.stdout": "b0234d5eb75100bbd7603460860b6bdc6e8240b61c2e9741060b5d3d865de4b3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-08-driver.npz": "22ca88afa65da194938c2b5f450d5ef90ed6d0e4c8ae8a605a16fa6c6896d98c",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-08-ledger.json": "4af43d14dedf2f8e3d32bf8f620ecca551b406f0eb25d1c5d57da691007dacb3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-08-ledger.npz": "ac692435497a36c5a7dfae1821fa52220bf03d3cbca9f73f2ebdb52e42e4b6db",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-09-collector.stdout": "ff5aeda3ec78b866dd71e6e1010f25cb536c38b6fc57160095cd77b30763cdf5",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-09-driver.npz": "96eac2210c44a788230757816b83af8b58997a36c653d0874d265624c62de707",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-09-ledger.json": "5d6feb8d87fd28b6b0938c5b755ff2fb556c51eb9ef8439d4ec7a016490f0af1",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/E3/cpu-09-ledger.npz": "02918a717339f10d4de9e515886e6c2908cf0e706d655da927570860d384511a",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/analyze.py": "6a91d4b1629103ee680b4f9668deffaeea9c1ef94a44af0bb276d331aac006bf",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-08-collector.stdout": "27a1bad932245e3fbc0fb5e5d52592909599d332fe3e18cc3a2b141012b67023",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-08-driver.npz": "3f1f07ae2bd36e153bb0deeeb682315bc8e970c8a8af13c0d65718366c49172c",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-08-ledger.json": "b091d5c0dcd53bd49ca82931eb515253a2b4ed7032f29f3eb434863dfe52c1e3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-08-ledger.npz": "ac692435497a36c5a7dfae1821fa52220bf03d3cbca9f73f2ebdb52e42e4b6db",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-09-collector.stdout": "7f580d13198da745ddb7517346ad4a69927ed8a57840c1388bc7858871ecaa47",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-09-driver.npz": "8e4aab73f88ebde37f658cd66dfe9d142419c7105058b77339c38ae70507a0ca",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-09-ledger.json": "c1bfd876d44818852bfab0865d1981f5cb8a286ffb237e3f2a88c3e730e4d218",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/candidate/cpu-09-ledger.npz": "02918a717339f10d4de9e515886e6c2908cf0e706d655da927570860d384511a",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/collect.py": "51ab1ba5fac08a26556b8e852293ffc13a3b14c05f3084bda60e5ba4e63546aa",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/cpu-08-recipe.json": "6cf9e14bc863b34dca0e999a983892f12561f1819c90acf7c22c49b85f598db7",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/cpu-09-recipe.json": "24d5ae132dde3b78cd08366f973480b3cf1388f2c898600eff9aa53ed2942a36",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/execution.log": "4554782ae129720a9907f094fca6f79dd91d8ecd7ed016979962aa4d7385e6d1",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/findings.json": "f27a92bdefde566c6a1175560cdae93ac7a868db2ee3e7a629d31d1c498bcec3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/findings.md": "51ceceba3fe545a542b90f7839c9399633e599db1a24875a0db6d062945df1ad",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/original-frozen-report.FAILED.json": "033734db94902c8878b0f05bde0454b1ed7cd897a5deb35842ecc81b1541963a",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/original-static-access-report.FAILED.json": "4d422f6673b9fb16cca5c76987364c1f4642ec0951fee59d535caf94a14a0bea",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-08-collector.stdout": "ffa88b496b976acb3bad71fa4569e5afb725147803a08965cce1b719096b6540",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-08-driver.npz": "39c6aba4b254998b6de2efb36bff2f9c4b3e93849c219516b8deac9396bf2e7d",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-08-ledger.json": "21d6b89b7e7114e369ee452096f2de9e505fc41164dcce336384b14da7e80e30",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-08-ledger.npz": "16c3f0d860c52cc71372c8e1a5973684d0dd9234b74ba7cc342c4508741c2565",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-09-collector.stdout": "eba60b08fdc6b762277795ae409d38168c79b994375c1caa5829347c4d49ca2e",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-09-driver.npz": "b9d8cd55266966b14f2630eddc8422f0e5d4543adc8b1d4a3332795d54740e93",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-09-ledger.json": "92961dd103c859cc24b503256bcd7d08abf88032ba81ae21c51a0315593173fd",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/parent/cpu-09-ledger.npz": "f73604351b223c954259433c67acb2cf400996bb3fe651921a07c82d90d423cf",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/source-closure.json": "b539a640e7725715762936ac8ee8c58653c0636431e37b7de4693af8eae0e875",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-08-collector.stdout": "51610079de36fa9bd3742218e8b692692645274b0d21c02256928c3366b684f3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-08-driver.npz": "bfdf146f67fe9a091072c3e32e8032f592a5b14b6d3aab5eaa4981de590ed6e4",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-08-ledger.json": "e4b236ae1baeec67945d991d346f432531bb25cd582b37296ee8dd708345f2b2",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-08-ledger.npz": "ac692435497a36c5a7dfae1821fa52220bf03d3cbca9f73f2ebdb52e42e4b6db",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-09-collector.stdout": "47c7bc79b4a68cfd216ed5c37c5d833d20aa645b8e4011f82212145a9538fbab",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-09-driver.npz": "656548e602f3ceeaab604fed5800e207b09c6f3a72cde088c83d436d85a50b03",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-09-ledger.json": "3910e3dbb7814d5f50213c3265f1ab25552b981acdc8a0ac981d94bd8d3bdab2",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E2/cpu-09-ledger.npz": "02918a717339f10d4de9e515886e6c2908cf0e706d655da927570860d384511a",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-08-collector.stdout": "b0234d5eb75100bbd7603460860b6bdc6e8240b61c2e9741060b5d3d865de4b3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-08-driver.npz": "22ca88afa65da194938c2b5f450d5ef90ed6d0e4c8ae8a605a16fa6c6896d98c",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-08-ledger.json": "4af43d14dedf2f8e3d32bf8f620ecca551b406f0eb25d1c5d57da691007dacb3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-08-ledger.npz": "ac692435497a36c5a7dfae1821fa52220bf03d3cbca9f73f2ebdb52e42e4b6db",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-09-collector.stdout": "ff5aeda3ec78b866dd71e6e1010f25cb536c38b6fc57160095cd77b30763cdf5",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-09-driver.npz": "96eac2210c44a788230757816b83af8b58997a36c653d0874d265624c62de707",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-09-ledger.json": "5d6feb8d87fd28b6b0938c5b755ff2fb556c51eb9ef8439d4ec7a016490f0af1",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/E3/cpu-09-ledger.npz": "02918a717339f10d4de9e515886e6c2908cf0e706d655da927570860d384511a",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-08-collector.stdout": "27a1bad932245e3fbc0fb5e5d52592909599d332fe3e18cc3a2b141012b67023",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-08-driver.npz": "3f1f07ae2bd36e153bb0deeeb682315bc8e970c8a8af13c0d65718366c49172c",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-08-ledger.json": "b091d5c0dcd53bd49ca82931eb515253a2b4ed7032f29f3eb434863dfe52c1e3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-08-ledger.npz": "ac692435497a36c5a7dfae1821fa52220bf03d3cbca9f73f2ebdb52e42e4b6db",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-09-collector.stdout": "7f580d13198da745ddb7517346ad4a69927ed8a57840c1388bc7858871ecaa47",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-09-driver.npz": "8e4aab73f88ebde37f658cd66dfe9d142419c7105058b77339c38ae70507a0ca",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-09-ledger.json": "c1bfd876d44818852bfab0865d1981f5cb8a286ffb237e3f2a88c3e730e4d218",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/candidate/cpu-09-ledger.npz": "02918a717339f10d4de9e515886e6c2908cf0e706d655da927570860d384511a",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-08-collector.stdout": "ffa88b496b976acb3bad71fa4569e5afb725147803a08965cce1b719096b6540",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-08-driver.npz": "39c6aba4b254998b6de2efb36bff2f9c4b3e93849c219516b8deac9396bf2e7d",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-08-ledger.json": "21d6b89b7e7114e369ee452096f2de9e505fc41164dcce336384b14da7e80e30",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-08-ledger.npz": "16c3f0d860c52cc71372c8e1a5973684d0dd9234b74ba7cc342c4508741c2565",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-09-collector.stdout": "eba60b08fdc6b762277795ae409d38168c79b994375c1caa5829347c4d49ca2e",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-09-driver.npz": "b9d8cd55266966b14f2630eddc8422f0e5d4543adc8b1d4a3332795d54740e93",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-09-ledger.json": "92961dd103c859cc24b503256bcd7d08abf88032ba81ae21c51a0315593173fd",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/parent/cpu-09-ledger.npz": "f73604351b223c954259433c67acb2cf400996bb3fe651921a07c82d90d423cf",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing-execution.log": "4554782ae129720a9907f094fca6f79dd91d8ecd7ed016979962aa4d7385e6d1",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/before-hashes.json": "b7a3b3cd0e4bcc2719eb8ee946736640c16aed2641fe7fb154c93bdd8b9e4292",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/before-inputs.json": "30526ea26feb63375f0820c72c3a694031465b540d1e6c4a27a5ea909521bf08",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/before-products.json": "13a685d6a75af86f3ecceb1b3d597d1b0a9595525b508b41051ce6ef2d3eee0a",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/before-recipes.json": "c446c97c1c8507fa6d97893b6db7e22aba3c9c383170f86e73db4b15b5c0c502",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/before-resets.json": "eac37c561a7bee828510ceb8b5ae3c500f1e15a4dde65674867331ce1001c0c6",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/before-traces.json": "ac4645068789af78e10748170afe58402c60dffdb7a356f660ab693a8e5c9b3c",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-00.npz": "e7aa827f5240a4a52ff70ecd585cda2702e943c17c35b5c618cd19afc197db6b",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-01.npz": "84b4812dedab70bab105662b9a26bb8c7cd376b4963b4d77a63bca2f7123409a",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-02.npz": "6dd4db005688aa1bb93b9ed250868e3f5fd233241b59d155c5dd68471bf070d6",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-03.npz": "d447aa3bc0abae294227d59fee910525e18b4dc3321a023fcbf4776dcd097a17",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-04.npz": "501bc800ab4e1b4c4e6dff9591470fec9b2ead47e054841a82f1a1789dde3bb8",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-05.npz": "39cc9b48f6bbc948531245e5cba1ed5784298c413846185cb58efeccf2e3b503",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-06.npz": "b06f102f34cb010726945c76bb8a31af278d2b3adf1ba878747079b28a25e403",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-07.npz": "da87fd5b971a88fcb1b6baf8602b0f4e78014e21202279ef8df2b107d7a3a1cd",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-08.npz": "dcf4bc6174ab00c9356f7cf41552b001df842b2c6761415492c9eb6de07fab18",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/cpu-09.npz": "d19ebe7f64f339dbea93a258fd1515173daa1b5a36899c34f7273684bb8406ae",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access/manifest.json": "47442e6c155541b0ef2c355ce594872f48fb2f2eeeabd66daa87c5cfc0c19acf",
    "runs/episode-lanes/2026-10-02/implementation/parent/static-access.log": "8c2d29fcf99ec2d599a7ae7facc775bcbaffd881d095d53108dd4f6ce7f257a5",
    "runs/episode-lanes/2026-10-02/implementation/qualification/frozen-oracle/output.log": "4c1c398f5eb75dcd0b2c97cb2653fce5773e10821f83cd17a825f316217edec7",
    "runs/episode-lanes/2026-10-02/implementation/qualification/static-access/output.log": "ccd2879d66f7c2b7ea557366f8692665d3312d3b6ea4dcda04065d400a9ed9bb",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/capture-final.py": "71bf51871b2ec713e65a66c52d40c7e43b9e5690f338abc9f53ad17eac8ee616",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-08-collector.stdout": "27a1bad932245e3fbc0fb5e5d52592909599d332fe3e18cc3a2b141012b67023",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-08-driver.npz": "3f1f07ae2bd36e153bb0deeeb682315bc8e970c8a8af13c0d65718366c49172c",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-08-ledger.json": "b091d5c0dcd53bd49ca82931eb515253a2b4ed7032f29f3eb434863dfe52c1e3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-08-ledger.npz": "ac692435497a36c5a7dfae1821fa52220bf03d3cbca9f73f2ebdb52e42e4b6db",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-09-collector.stdout": "7f580d13198da745ddb7517346ad4a69927ed8a57840c1388bc7858871ecaa47",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-09-driver.npz": "8e4aab73f88ebde37f658cd66dfe9d142419c7105058b77339c38ae70507a0ca",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-09-ledger.json": "c1bfd876d44818852bfab0865d1981f5cb8a286ffb237e3f2a88c3e730e4d218",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-candidate/cpu-09-ledger.npz": "02918a717339f10d4de9e515886e6c2908cf0e706d655da927570860d384511a",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-execution.json": "f4bac026159947bdc9fb0d7b3e1fe09af857a86f932abe712a4ec19738d992b7",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-execution.log": "4190b1ed28f2e14ba9ef1363f4b3f66a6ed6a956a49fd098fef70e05691f1a17",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/final-source-closure.json": "5861b87c30cc4fbd51fa68566f202b5c8414c616c6f130fe6fbd841213a6c2cd",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/freeze-final-spec.py": "5ed78567794b637a231fe5392c02e9c10424848d7ff66d3dd1570ab7e97350d9",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-08-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-08-collector.stdout": "27a1bad932245e3fbc0fb5e5d52592909599d332fe3e18cc3a2b141012b67023",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-08-driver.npz": "3f1f07ae2bd36e153bb0deeeb682315bc8e970c8a8af13c0d65718366c49172c",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-08-ledger.json": "b091d5c0dcd53bd49ca82931eb515253a2b4ed7032f29f3eb434863dfe52c1e3",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-08-ledger.npz": "ac692435497a36c5a7dfae1821fa52220bf03d3cbca9f73f2ebdb52e42e4b6db",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-09-collector.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-09-collector.stdout": "7f580d13198da745ddb7517346ad4a69927ed8a57840c1388bc7858871ecaa47",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-09-driver.npz": "8e4aab73f88ebde37f658cd66dfe9d142419c7105058b77339c38ae70507a0ca",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-09-ledger.json": "c1bfd876d44818852bfab0865d1981f5cb8a286ffb237e3f2a88c3e730e4d218",
    "runs/episode-lanes/2026-10-02/implementation/causal/inherited-terminal-streams/standing/final-candidate/cpu-09-ledger.npz": "02918a717339f10d4de9e515886e6c2908cf0e706d655da927570860d384511a"
  },
  "checker_sha256": "05fa08a7d36fdc0222339fc23f867c971d221a0270b41ab0784f21ca86397a27",
  "scope": "Seven literal coordinates only. Two original commands remain FAILED. No stream allowance, CUDA, learning or convergence claim.",
  "final_source_prerequisite": "Final commit and four actual bridges are captured and pinned. Root must prospectively register this exact spec digest before qualification GO."
}
```

## Frozen checker source

```python
"""Prospective PDR-0161 checker. Original literal gates stay FAILED.

Only main() qualifies. Preparing, formatting or reviewing this file does not run
qualification. All corruptions are private in-memory copies of loaded evidence.
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[5]
BASE = ROOT / "runs/episode-lanes/2026-10-02/implementation"
PARENT = BASE / "parent/static-access"
CANDIDATE = BASE / "candidate/static-access"
FROZEN = ROOT / "runs/differential/20261002-090009"
SIDES = ("parent", "E2", "E3", "candidate")
SHAS = {
    "parent": "880f9c90f65aa646a0da04d7ca2ef92e48f85caa",
    "E2": "10cfc83495146f49d8fd8aeb7f3ba149ab087f54",
    "E3": "904f166ad17f201619e60e6284fd1e41c492c77b",
    "candidate": "8e3ca306d6f615bd272bb1c8d51b071b74686877",
}
LITERAL_COORDINATES = {"cpu-08": [[99, 0], [99, 1], [99, 3]], "cpu-09": [[99, 0], [99, 1], [99, 2], [99, 3]]}
COUNTS = {"cpu-08": [49, 51, 100, 54], "cpu-09": [65, 67, 62, 60]}
COMPONENTS = ("extrinsic", "intrinsic", "intrinsic_raw", "shaping")
REQUIRED_CONTROLS = (
    "live_reward_one_float32_ulp",
    "retained_false_bonus",
    "dropped_expected_difference",
    "swapped_lane_coordinates",
    "undesigned_dead_reward",
    "undesigned_signed_zero",
    "wrong_designated_magnitude",
    "wrong_designated_signed_zero",
    "changed_observation",
    "changed_action",
    "changed_done",
    "changed_hash",
    "nonfinite_reward",
    "nonfinite_observation",
    "changed_reward_dtype",
    "changed_reward_shape",
    "forged_active_entry",
    "forged_new_terminal",
    "forged_new_retirement",
    "advanced_completed_counter",
    "wrong_independent_survival",
    "changed_world_tick",
    "changed_lifespan",
    "changed_raw_DAC",
    "changed_E2_component",
    "changed_E3_component",
    "genuine_retirement_reward_corruption",
    "stale_allowance",
    "unused_expected_coordinate",
    "swapped_allowance_coordinates",
    "omitted_static_trace",
    "omitted_inventory",
    "changed_identity_reading",
    "omitted_reset",
    "changed_reset",
    "changed_registered_verdict",
    "omitted_cuda_skip",
    "changed_skip_reason",
    "changed_source_binding",
    "changed_config_binding",
    "changed_import_root",
    "changed_original_dirty_flag",
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def load_npz(path):
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key].copy() for key in data.files}


def exact(left, right):
    return left.dtype == right.dtype and left.shape == right.shape and left.tobytes() == right.tobytes()


def metadata(data):
    require(data["meta"].shape == () and data["meta"].dtype.kind == "U", "invalid trace metadata shape/dtype")
    return json.loads(str(data["meta"]))


def entry_masks(dones):
    require(not np.any(dones[:-1] & ~dones[1:]), "done trajectory is not sticky")
    return np.concatenate([np.ones((1, 4), dtype=bool), ~dones[:-1]])


def finite_json(value):
    if isinstance(value, dict):
        for item in value.values():
            finite_json(item)
    elif isinstance(value, list):
        for item in value:
            finite_json(item)
    elif isinstance(value, float):
        require(np.isfinite(value), "nonfinite causal numeric value")


def vector(values, dtype, name):
    require(isinstance(values, list) and len(values) == 4, f"{name}: malformed vector")
    if dtype == np.bool_:
        require(all(type(value) is bool for value in values), f"{name}: not literal boolean flags")
    elif dtype == np.int64:
        require(all(type(value) is int for value in values), f"{name}: not literal integer counts")
    else:
        require(all(type(value) in (int, float) for value in values), f"{name}: not numeric values")
    data = np.asarray(values, dtype=dtype)
    require(np.isfinite(data).all(), f"{name}: nonfinite vector")
    return data


def validate_trace(data, params):
    require(set(data) == {"meta", "obs", "actions", "dones", "rewards"}, "omitted/extra trace array")
    finite_json(metadata(data))
    require(metadata(data)["params"] == params, "trace recipe changed")
    for field, dtype, shape in (
        ("rewards", np.float32, (100, 4)),
        ("actions", np.int64, (100, 4)),
        ("dones", np.bool_, (100, 4)),
    ):
        require(data[field].dtype == dtype and data[field].shape == shape, f"{field}: invalid shape/dtype")
    obs = data["obs"]
    require(obs.dtype == np.float32 and obs.ndim == 3 and obs.shape[:2] == (101, 4) and obs.shape[2] > 0, "obs: invalid shape/dtype")
    require(all(np.isfinite(data[field]).all() for field in ("obs", "actions", "dones", "rewards")), "nonfinite trace array")
    entry_masks(data["dones"])


def compare_rewards(old, new, coordinates):
    """Full bytes after ONLY literal substitutions, including all signed zero bits."""
    require(old.dtype == np.float32 and new.dtype == np.float32 and old.shape == new.shape == (100, 4), "reward shape/dtype changed")
    require(np.isfinite(old).all() and np.isfinite(new).all(), "nonfinite reward")
    require(len({tuple(coord) for coord in coordinates}) == len(coordinates), "duplicate unused allowance")
    expected = old.copy()
    for coord in coordinates:
        require(len(coord) == 2 and all(type(value) is int for value in coord), "malformed literal coordinate")
        index, lane = coord
        require(0 <= index < 100 and 0 <= lane < 4, "out-of-bounds literal coordinate")
        require(int(old[index, lane].view(np.uint32)) == 0x3F800000, "unused expected coordinate / wrong old bits")
        require(int(new[index, lane].view(np.uint32)) == 0x00000000, "missing expected difference / wrong new bits")
        expected[index, lane] = np.float32(0.0)
    require(exact(expected, new), "undesigned reward byte changed outside literal substitutions")


def bank_load():
    bank = {
        "source_closure": read_json(OUT / "source-closure.json"),
        "static_report": read_json(CANDIDATE / "report.json"),
        "frozen_report": read_json(FROZEN / "report.json"),
        "manifest": read_json(PARENT / "manifest.json"),
        "recipes": read_json(PARENT / "before-recipes.json"),
        "before_hashes": read_json(PARENT / "before-hashes.json"),
        "before_inputs": read_json(PARENT / "before-inputs.json"),
        "before_products": read_json(PARENT / "before-products.json"),
        "before_resets": read_json(PARENT / "before-resets.json"),
        "before_traces": read_json(PARENT / "before-traces.json"),
        "after_census": read_json(CANDIDATE / "after-census.json"),
        "after_inputs": read_json(CANDIDATE / "after-inputs.json"),
        "after_resets": read_json(CANDIDATE / "after-resets.json"),
        "after_traces": read_json(CANDIDATE / "after-traces.json"),
        "static": {},
        "standing": {},
        "causal": {},
    }
    for index, recipe in enumerate(bank["recipes"]["traces"]):
        key = f"cpu-{index:02d}"
        stem = recipe["cell_id"].replace(":", "_")
        bank["static"][key] = {side: load_npz(path / f"{key}.npz") for side, path in (("old", PARENT), ("new", CANDIDATE))}
        bank["standing"][key] = {side: load_npz(FROZEN / f"{stem}.{side}.npz") for side in ("old", "new", "actions")}
    for mode in ("static", "standing"):
        directory = OUT if mode == "static" else OUT / "standing"
        bank["causal"][mode] = {}
        for key in LITERAL_COORDINATES:
            bank["causal"][mode][key] = {
                side: {
                    "driver": load_npz(directory / side / f"{key}-driver.npz"),
                    "collected": load_npz(directory / side / f"{key}-ledger.npz"),
                    "ledger": read_json(directory / side / f"{key}-ledger.json"),
                }
                for side in SIDES
            }
    bank["final_source_binding"] = read_json(OUT / "final-source-closure.json")
    bank["final"] = {}
    for mode in ("static", "standing"):
        directory = OUT if mode == "static" else OUT / "standing"
        bank["final"][mode] = {
            key: {
                "driver": load_npz(directory / "final-candidate" / f"{key}-driver.npz"),
                "collected": load_npz(directory / "final-candidate" / f"{key}-ledger.npz"),
                "ledger": read_json(directory / "final-candidate" / f"{key}-ledger.json"),
            }
            for key in LITERAL_COORDINATES
        }
    return bank


def validate_bindings(spec):
    """Bind retained bank and physical imports to the declared committed sources."""
    require(spec["source_shas"] == SHAS, "stale source allowance")
    require(spec["exact_changed_coordinates"] == LITERAL_COORDINATES, "stale/unused/swapped coordinate allowance")
    require(spec["actual_counts"] == COUNTS, "stale survival allowance")
    require(tuple(spec["negative_controls"]) == REQUIRED_CONTROLS, "omitted/stale corruption control")
    require(
        spec["lifespan"] == 100 and spec["exact_old_bits"] == "0x3f800000" and spec["exact_new_bits"] == "0x00000000",
        "stale literal value/lifespan allowance",
    )
    # The specification binds the consumer too; accepting edited code needs new prospective review.
    require(digest(Path(__file__)) == spec["checker_sha256"], "unreviewed checker bytes")
    for relative, expected in spec["artifact_sha256"].items():
        require(digest(ROOT / relative) == expected, f"changed original evidence: {relative}")
    for relative, expected in spec["config_sha256"].items():
        require(digest(ROOT / relative) == expected, f"changed actual config bytes: {relative}")
    require(spec["source_bindings"] == read_json(OUT / "source-closure.json"), "changed source/import closure binding")
    require(spec["final_source_binding"] == read_json(OUT / "final-source-closure.json"), "changed final source binding")
    final = spec["final_source_binding"]
    require(len(final["sha"]) == 40 and all(value in "0123456789abcdef" for value in final["sha"]), "final source SHA not preregistered")
    require(final["source_root"] == str(ROOT / "src"), "wrong final physical/import root")
    require(
        spec["final_source_differences"]
        and set(spec["final_source_differences"]) <= {"src/townlet/demo/database.py", "src/townlet/training/episode_accounting.py"},
        "unexpected final numerical source changes",
    )
    original_closure = spec["source_bindings"]["candidate"]["closure"]
    changed = {
        name: {"retained": original_closure.get(name), "final": final["closure"].get(name)}
        for name in set(original_closure) | set(final["closure"])
        if original_closure.get(name) != final["closure"].get(name)
    }
    require(changed == spec["final_source_differences"], "final source difference fence changed")
    source_bindings = {**spec["source_bindings"], "final-candidate": final}
    for side, binding in source_bindings.items():
        require(binding["sha"] == (final["sha"] if side == "final-candidate" else SHAS[side]), "wrong causal source SHA")
        tree = subprocess.check_output(["git", "rev-parse", f'{binding["sha"]}:src'], cwd=ROOT, text=True).strip()
        require(tree == binding["src_tree"], "wrong committed source tree")
        archive = subprocess.check_output(["git", "archive", binding["sha"], "src"], cwd=ROOT)
        require(hashlib.sha256(archive).hexdigest() == binding["archive_sha256"], "changed committed source archive")
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            committed = {
                member.name: hashlib.sha256(tar.extractfile(member).read()).hexdigest() for member in tar.getmembers() if member.isfile()
            }
        require(committed == binding["closure"], "incomplete committed source closure")
        source_root = Path(spec["verification_roots"][side])
        imported = {
            f"src/{path.relative_to(source_root).as_posix()}": digest(path)
            for path in source_root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        require(imported == committed, "actual imported source differs from committed full closure")
    e2 = spec["source_bindings"]["E2"]
    require(
        subprocess.check_output(["git", "rev-parse", f'{SHAS["E2"]}^'], cwd=ROOT, text=True).strip() == e2["direct_parent_sha"],
        "wrong E2 immediate parent",
    )
    require(e2["direct_parent_src_tree"] == spec["source_bindings"]["parent"]["src_tree"], "E2 precursor source changed")
    require(
        subprocess.check_output(["git", "rev-parse", f'{e2["direct_parent_sha"]}:src'], cwd=ROOT, text=True).strip()
        == e2["direct_parent_src_tree"],
        "unverified E2 immediate-parent runtime",
    )
    require(
        (OUT / "original-static-access-report.FAILED.json").read_bytes() == (CANDIDATE / "report.json").read_bytes(),
        "static failed-report custody changed",
    )
    require(
        (OUT / "original-frozen-report.FAILED.json").read_bytes() == (FROZEN / "report.json").read_bytes(),
        "standing failed-report custody changed",
    )


def validate_inventories(bank, spec):
    require(bank["source_closure"] == spec["source_bindings"], "changed source binding")
    require(bank["final_source_binding"] == spec["final_source_binding"], "changed final source binding")
    require(bank["recipes"] == spec["recipes"], "omitted/changed declared recipes")
    require(
        len(bank["recipes"]["census"]) == 31 and len(bank["recipes"]["resets"]) == 11 and len(bank["recipes"]["traces"]) == 10,
        "incomplete 31/11/10 recipe inventory",
    )
    report = bank["static_report"]
    require(report == spec["static_report"], "original static report changed")
    require(
        report["case_count"] == 31 and report["reading_count"] == 884 and report["reset_count"] == 11 and report["cpu_count"] == 10,
        "static invariant counts changed",
    )
    require(report["baseline_source"] == SHAS["parent"] and report["source_commit"] == SHAS["candidate"], "wrong static source")
    require(
        report["trace_failed"] is True and report["qualified"] is False and report["reset_failed"] is False,
        "original failed static verdict hidden",
    )
    require(report["changes"] == report["unattributed"] == report["stale_attributions"] == [], "identity attribution changed")
    hashes, census = bank["before_hashes"], bank["after_census"]
    require(
        hashes["source_commit"] == SHAS["parent"] and hashes["case_count"] == 31 and hashes["reading_count"] == 884,
        "wrong parent census identity",
    )
    require(
        len(hashes["cases"]) == len(census["cases"]) == 31 and hashes["cases"] == census["cases"], "omitted/changed full census reading"
    )
    require(sum(len(row["hashes"]) for row in hashes["cases"]) == 884, "omitted identity reading")
    require(
        [{"pack": row["pack"], "primary_level": row["primary_level"]} for row in hashes["cases"]] == bank["recipes"]["census"],
        "census recipe inventory changed",
    )
    require(census["product_changes"] == [], "product readings changed")
    require(
        bank["before_products"]["source_commit"] == SHAS["parent"] and len(bank["before_products"]["cases"]) == 31,
        "omitted parent product inventory",
    )
    require(bank["before_inputs"]["source_commit"] == SHAS["parent"], "wrong input source identity")
    for relative, reading in bank["before_inputs"]["files"].items():
        require(
            hashlib.sha256(base64.b64decode(reading["bytes_base64"], validate=True)).hexdigest() == reading["sha256"],
            "parent config bytes/digest inconsistent",
        )
        require(bank["after_inputs"]["files"].get(relative) == reading["sha256"], "changed inherited authored config")
    require(bank["after_inputs"]["files"] == spec["config_sha256"], "config inventory changed")
    require(bank["after_inputs"]["changes"] == spec["new_authored_config_changes"], "unexpected authored input change")
    before, after = bank["before_resets"], bank["after_resets"]
    require(
        before["source_commit"] == SHAS["parent"] and len(before["cases"]) == len(after["cases"]) == 11 and after["failed"] is False,
        "omitted/failed reset inventory",
    )
    for old, new in zip(before["cases"], after["cases"], strict=True):
        require(new["changes"] == [] and new["readings"] == old, "reset readings changed")
    manifest = bank["manifest"]
    require(
        manifest["source_commit"] == SHAS["parent"] and manifest["source_root"] == str(ROOT) and manifest["trace_base"] == str(PARENT),
        "wrong parent bank source/import root",
    )
    for entry in manifest["reports"].values():
        relative = (PARENT / entry["file"]).relative_to(ROOT).as_posix()
        require(spec["artifact_sha256"][relative] == entry["sha256"], "parent manifest binding changed")
    bt, at = bank["before_traces"], bank["after_traces"]
    require(
        bt["source_commit"] == SHAS["parent"] and len(bt["cells"]) == len(at["cells"]) == 10 and at["failed"] is True,
        "omitted/hidden raw trace failure inventory",
    )
    keys = {f"cpu-{index:02d}" for index in range(10)}
    require(set(bank["static"]) == set(bank["standing"]) == keys, "omitted raw CPU trace")
    for index, recipe in enumerate(bank["recipes"]["traces"]):
        key = f"cpu-{index:02d}"
        old, new = bt["cells"][index], at["cells"][index]
        require(
            old["cell_id"] == new["cell_id"] == recipe["cell_id"] and old["file"] == new["file"] == f"{key}.npz",
            "trace inventory reordered/substituted",
        )
        for side, directory, reading in (("old", PARENT, old), ("new", CANDIDATE, new)):
            data = bank["static"][key][side]
            require(
                metadata(data)["code_root"] == str(ROOT / "src") and metadata(data)["pack_root"] == str(ROOT),
                "original trace source/import roots changed",
            )
            require(metadata(data)["hashes"] == reading["hashes"], "trace hash metadata detached from inventory")
            require(
                spec["artifact_sha256"][(directory / f"{key}.npz").relative_to(ROOT).as_posix()] == reading["file_sha256"],
                "raw trace file detached from inventory",
            )
        for field in ("obs", "actions", "dones", "rewards"):
            require(
                new["comparison"][field]["equal"] is (field != "rewards" or key not in LITERAL_COORDINATES),
                "original stream mismatch inventory changed",
            )
    frozen = bank["frozen_report"]
    require(frozen == spec["frozen_report"], "original frozen report/dirty flags changed")
    require(
        frozen["meta"]["new_commit"] == SHAS["candidate"]
        and frozen["meta"]["new_dirty"] is True
        and frozen["meta"]["oracle_commit"] == "4222a9176e68e232a0e46c7004183440e27f22c3",
        "standing source/dirty flag changed",
    )
    require(len(frozen["verdicts"]) == 20, "omitted standing verdict")
    expected = {}
    for index, recipe in enumerate(bank["recipes"]["traces"]):
        expected[recipe["cell_id"]] = "DIVERGE" if f"cpu-{index:02d}" in LITERAL_COORDINATES else "DIVERGED_AS_REGISTERED"
        expected[recipe["cell_id"].replace(":cpu:", ":cuda:")] = "SKIPPED"
    require({row["cell_id"]: row["kind"] for row in frozen["verdicts"]} == expected, "changed eight CPU/two DIVERGE/ten skip statuses")
    require(
        all(row["detail"]["reason"] == "cuda not requested" for row in frozen["verdicts"] if row["kind"] == "SKIPPED"),
        "missing explicit CUDA skip reason",
    )


def validate_causal(bank, spec, mode, key, params):
    records = bank["causal"][mode][key]
    old, new = bank[mode][key]["old"], bank[mode][key]["new"]
    entry = entry_masks(old["dones"])
    counts = entry.astype(np.int64).cumsum(axis=0)
    require(counts[-1].tolist() == COUNTS[key], "wrong independently derived survival")
    require(exact(old["rewards"][entry], new["rewards"][entry]), "changed live reward")
    parent = records["parent"]["driver"]
    require(exact(old["rewards"], parent["rewards"]), "oracle/parent reward bridge changed")
    require(
        exact(new["obs"], parent["obs"]) and metadata(new)["hashes"] == metadata(parent)["hashes"],
        "registered oracle observation/hash residual expanded",
    )
    config_prefix = params["pack"] + "/"
    expected_config = {path[len(config_prefix) :]: sha for path, sha in spec["config_sha256"].items() if path.startswith(config_prefix)}
    for side in SIDES:
        driver, collected, ledger = (records[side][name] for name in ("driver", "collected", "ledger"))
        validate_trace(driver, params)
        require(set(collected) == {"obs", "actions", "dones", "rewards"}, "collector arrays omitted")
        require(all(exact(driver[field], collected[field]) for field in collected), "observer changed actual driver execution")
        require(all(exact(old[field], driver[field]) for field in ("actions", "dones")), "source action/done bridge changed")
        require(
            exact(parent["obs"], driver["obs"]) and metadata(driver)["hashes"] == metadata(parent)["hashes"],
            "source observation/compiled hash chain changed",
        )
        require(exact(driver["rewards"], old["rewards"] if side == "parent" else new["rewards"]), "wrong causing commit reward chain")
        require(
            metadata(driver)["code_root"] == spec["source_bindings"][side]["source_root"] and metadata(driver)["pack_root"] == str(ROOT),
            "actual driver import root changed",
        )
        action_sha = hashlib.sha256(old["actions"].tobytes()).hexdigest()
        require(metadata(driver)["action_source"] == "scripted:" + action_sha[:16], "not the retained actual action stream")
        require(
            ledger["imported_source_root"] == spec["source_bindings"][side]["source_root"] and ledger["params"] == params,
            "causal import/config recipe changed",
        )
        require(ledger["configured_lifespan"] == 100 and ledger["config_inputs"] == expected_config, "causal lifespan/config bytes changed")
        finite_json(ledger)
        require(len(ledger["rows"]) == 100, "causal row omitted")
        for index, row in enumerate(ledger["rows"]):
            prefix = f"{mode}/{key}/{side}/{index}"
            require(row["index"] == index and row["world_tick"] == index + 1, prefix + ": changed world tick")
            vtc = vector(row["vtc_dones"], np.bool_, prefix)
            authored = entry[index] & vtc
            retired = entry[index] & ~authored & (counts[index] >= 100)
            terminal = entry[index] & old["dones"][index]
            require(exact(vector(row["active_on_entry_independent"], np.bool_, prefix), entry[index]), prefix + ": forged eligibility")
            require(exact(vector(row["new_terminal_independent"], np.bool_, prefix), terminal), prefix + ": forged terminal")
            require(exact(vector(row["authored_terminal_independent"], np.bool_, prefix), authored), prefix + ": forged authored ending")
            require(exact(vector(row["independent_counts"], np.int64, prefix), counts[index]), prefix + ": wrong survival")
            actual = np.full(4, index + 1, dtype=np.int64) if side == "parent" else counts[index]
            require(
                exact(vector(row["actual_step_counts"], np.int64, prefix), actual)
                and exact(vector(row["dac"]["step_counts"], np.int64, prefix), actual),
                prefix + ": completed counter advanced",
            )
            require(exact(vector(row["dones"], np.bool_, prefix), old["dones"][index]), prefix + ": final dones detached")
            require(exact(vector(row["dac"]["dones"], np.bool_, prefix), vtc), prefix + ": raw terminal stage detached")
            require(np.array_equal(vtc | retired, old["dones"][index]), prefix + ": ending/retirement causality changed")
            if side == "parent":
                require(row["events_present"] == {}, prefix + ": fabricated parent interface")
                bonus = actual >= 100
            else:
                events = row["events_present"]
                require(set(events) == {"active_on_entry", "newly_terminal", "newly_retired"}, prefix + ": event interface omitted")
                for name, expected in (("active_on_entry", entry[index]), ("newly_terminal", terminal), ("newly_retired", retired)):
                    require(exact(vector(events[name], np.bool_, prefix), expected), prefix + ": forged " + name)
                bonus = retired
            require(set(row["dac"]["components"]) == set(row["components"]) == set(COMPONENTS), prefix + ": omitted contributor")
            raw = vector(row["dac"]["reward"], np.float32, prefix)
            raw_components = {name: vector(row["dac"]["components"][name], np.float32, prefix) for name in COMPONENTS}
            require(
                exact(raw, raw_components["extrinsic"] + raw_components["intrinsic"] + raw_components["shaping"]),
                prefix + ": raw DAC/components inconsistent",
            )
            for name in COMPONENTS:
                require(
                    exact(
                        raw_components[name],
                        vector(records["parent"]["ledger"]["rows"][index]["dac"]["components"][name], np.float32, prefix),
                    ),
                    prefix + ": raw contributor chain changed",
                )
                expected_component = raw_components[name].copy()
                if side in ("E3", "candidate") and name == "extrinsic":
                    expected_component[bonus] += np.float32(1.0)
                require(
                    exact(vector(row["components"][name], np.float32, prefix), expected_component),
                    prefix + ": composed contributor changed",
                )
            expected_reward = raw.copy()
            expected_reward[bonus] += np.float32(1.0)
            require(
                exact(vector(row["reward"], np.float32, prefix), expected_reward) and exact(expected_reward, driver["rewards"][index]),
                prefix + ": raw-to-published reward causality changed",
            )
            expected_weights = entry[index].astype(np.float32) if side in ("E3", "candidate") else np.ones(4, dtype=np.float32)
            require(
                exact(vector(row["intrinsic_weights"], np.float32, prefix), expected_weights), prefix + ": intrinsic eligibility changed"
            )
            if side in ("E3", "candidate"):
                require(
                    exact(
                        vector(row["reward"], np.float32, prefix),
                        vector(row["components"]["extrinsic"], np.float32, prefix)
                        + vector(row["components"]["intrinsic"], np.float32, prefix)
                        + vector(row["components"]["shaping"], np.float32, prefix),
                    ),
                    prefix + ": canonical reward mismatch",
                )
    for index, lane in LITERAL_COORDINATES[key]:
        require(not entry[index, lane] and counts[index, lane] < 100, "changed coordinate was eligible for retirement")
        for side in SIDES:
            row = records[side]["ledger"]["rows"][index]
            require(
                row["dac"]["reward"][lane] == 0.0 and all(row["dac"]["components"][name][lane] == 0.0 for name in COMPONENTS),
                "changed coordinate has nonzero raw DAC contributor",
            )
            require(row["authored_terminal_independent"][lane] is False, "changed coordinate is a new authored ending")
            if side != "parent":
                require(
                    all(row["events_present"][name][lane] is False for name in row["events_present"]),
                    "changed completed coordinate has a new product event",
                )
    if key == "cpu-08":
        require(entry[99, 2] and counts[99, 2] == 100, "genuine retirement lost")
        require(
            int(old["rewards"][99, 2].view(np.uint32)) == int(np.float32(1.0099999904632568).view(np.uint32))
            and exact(old["rewards"][99:100, 2], new["rewards"][99:100, 2]),
            "genuine retirement reward corrupted",
        )
        require(
            all(records[side]["ledger"]["rows"][99]["events_present"]["newly_retired"][2] is True for side in SIDES[1:]),
            "genuine retirement event lost",
        )


def compare_bank(bank, spec):
    finite_json(bank)
    require(
        spec["source_shas"] == SHAS and spec["exact_changed_coordinates"] == LITERAL_COORDINATES and spec["actual_counts"] == COUNTS,
        "stale/unused/swapped allowance",
    )
    validate_inventories(bank, spec)
    for index, recipe in enumerate(bank["recipes"]["traces"]):
        key = f"cpu-{index:02d}"
        params = recipe["params"]
        require(
            {name: params[name] for name in ("num_agents", "steps", "seed", "device")}
            == {"num_agents": 4, "steps": 100, "seed": 42, "device": "cpu"},
            "wrong original recipe",
        )
        for mode in ("static", "standing"):
            old, new = bank[mode][key]["old"], bank[mode][key]["new"]
            validate_trace(old, params)
            validate_trace(new, params)
            require(all(exact(old[field], new[field]) for field in ("actions", "dones")), "changed full action/done stream")
            compare_rewards(old["rewards"], new["rewards"], LITERAL_COORDINATES.get(key, []))
            if mode == "static":
                require(
                    exact(old["obs"], new["obs"]) and metadata(old)["hashes"] == metadata(new)["hashes"],
                    "changed full parent observation/hash stream",
                )
            else:
                # Preserve registered old ABI residual by binding the candidate to the exact direct-parent bank.
                require(
                    exact(new["obs"], bank["static"][key]["new"]["obs"])
                    and metadata(new)["hashes"] == metadata(bank["static"][key]["new"])["hashes"],
                    "standing observation/hash residual expanded",
                )
                actions = bank[mode][key]["actions"]
                require(set(actions) == {"actions"} and exact(actions["actions"], old["actions"]), "frozen action recipe detached")
                require(exact(old["actions"], bank["static"][key]["old"]["actions"]), "recorded action arrays differ between banks")
                require(
                    exact(old["rewards"], bank["static"][key]["old"]["rewards"])
                    and exact(old["dones"], bank["static"][key]["old"]["dones"]),
                    "frozen/direct-parent terminal bridge changed",
                )
            if key in LITERAL_COORDINATES:
                validate_causal(bank, spec, mode, key, params)
                final = bank["final"][mode][key]
                retained = bank["causal"][mode][key]["candidate"]
                validate_trace(final["driver"], params)
                require(
                    metadata(final["driver"])["code_root"] == spec["final_source_binding"]["source_root"],
                    "final driver import root changed",
                )
                for field in ("obs", "actions", "dones", "rewards"):
                    require(
                        exact(final["driver"][field], retained["driver"][field])
                        and exact(final["collected"][field], retained["collected"][field]),
                        "final source numerical bridge changed",
                    )
                require(metadata(final["driver"]) == metadata(retained["driver"]), "final source trace metadata bridge changed")
                require(
                    json.dumps(final["ledger"], sort_keys=True) == json.dumps(retained["ledger"], sort_keys=True),
                    "final source full lifecycle/component ledger changed",
                )
    return {
        "static_cpu_cells": 10,
        "standing_cpu_cells": 10,
        "census_inventories": 31,
        "identity_readings": 884,
        "reset_recipes": 11,
        "standing_registered_cpu_verdicts_retained": 8,
        "explicit_cuda_skips": 10,
        "unique_literal_reward_changes": 7,
        "source_bridges": 4,
        "causal_source_executions": 20,
        "mandatory_final_source_bridges": 4,
        "final_source_sha": spec["final_source_binding"]["sha"],
        "changed_live_rewards": 0,
        "residual_reward_bytes_exact": True,
        "source_of_delta": SHAS["E2"],
        "original_gate_verdicts_replaced": False,
    }


def corrupt(name, bank, spec):
    """One deliberate violation per private copy; never writes originals."""
    value, allowance = copy.deepcopy(bank), copy.deepcopy(spec)
    new = value["static"]["cpu-08"]["new"]
    rows = value["causal"]["static"]["cpu-08"]["candidate"]["ledger"]["rows"]
    if name == "live_reward_one_float32_ulp":
        new["rewards"][0, 0] = np.nextafter(new["rewards"][0, 0], np.float32(np.inf))
    elif name in ("retained_false_bonus", "dropped_expected_difference"):
        new["rewards"][99, 0] = np.float32(1.0)
        if name == "dropped_expected_difference":
            value["static"]["cpu-08"]["old"]["rewards"][99, 0] = np.float32(0.0)
    elif name == "swapped_lane_coordinates":
        new["rewards"][99, 0], new["rewards"][99, 2] = new["rewards"][99, 2], new["rewards"][99, 0]
    elif name == "undesigned_dead_reward":
        new["rewards"][80, 0] = np.float32(0.25)
    elif name == "undesigned_signed_zero":
        new["rewards"][80, 0] = np.float32(-0.0)
    elif name == "wrong_designated_magnitude":
        new["rewards"][99, 0] = np.float32(-1.0)
    elif name == "wrong_designated_signed_zero":
        new["rewards"][99, 0] = np.float32(-0.0)
    elif name == "changed_observation":
        new["obs"][0, 0, 0] = np.nextafter(new["obs"][0, 0, 0], np.float32(np.inf))
    elif name == "changed_action":
        new["actions"][0, 0] += 1
    elif name == "changed_done":
        new["dones"][0, 0] = ~new["dones"][0, 0]
    elif name == "changed_hash":
        meta = metadata(new)
        meta["hashes"]["drive_hash"] = "forged"
        new["meta"] = np.array(json.dumps(meta))
    elif name == "nonfinite_reward":
        new["rewards"][0, 0] = np.float32(np.nan)
    elif name == "nonfinite_observation":
        new["obs"][0, 0, 0] = np.float32(np.inf)
    elif name == "changed_reward_dtype":
        new["rewards"] = new["rewards"].astype(np.float64)
    elif name == "changed_reward_shape":
        new["rewards"] = new["rewards"][:, :3]
    elif name in ("forged_active_entry", "forged_new_terminal", "forged_new_retirement"):
        field = {
            "forged_active_entry": "active_on_entry",
            "forged_new_terminal": "newly_terminal",
            "forged_new_retirement": "newly_retired",
        }[name]
        rows[99]["events_present"][field][0] = True
    elif name == "advanced_completed_counter":
        rows[99]["actual_step_counts"][0] += 1
    elif name == "wrong_independent_survival":
        rows[99]["independent_counts"][0] += 1
    elif name == "changed_world_tick":
        rows[99]["world_tick"] += 1
    elif name == "changed_lifespan":
        value["causal"]["static"]["cpu-08"]["candidate"]["ledger"]["configured_lifespan"] = 99
    elif name == "changed_raw_DAC":
        rows[99]["dac"]["reward"][0] = 0.01
    elif name in ("changed_E2_component", "changed_E3_component"):
        side = "E2" if name == "changed_E2_component" else "E3"
        value["causal"]["static"]["cpu-08"][side]["ledger"]["rows"][99]["components"]["extrinsic"][0] = 0.01
    elif name == "genuine_retirement_reward_corruption":
        new["rewards"][99, 2] = np.nextafter(new["rewards"][99, 2], np.float32(np.inf))
    elif name == "stale_allowance":
        allowance["source_shas"]["candidate"] = SHAS["parent"]
    elif name == "unused_expected_coordinate":
        allowance["exact_changed_coordinates"]["cpu-08"].append([80, 0])
    elif name == "swapped_allowance_coordinates":
        allowance["exact_changed_coordinates"]["cpu-08"][0] = [99, 2]
    elif name == "omitted_static_trace":
        del value["static"]["cpu-07"]
    elif name == "omitted_inventory":
        value["after_census"]["cases"].pop()
    elif name == "changed_identity_reading":
        value["after_census"]["cases"][0]["hashes"]["actions_hash"] = "forged"
    elif name == "omitted_reset":
        value["after_resets"]["cases"].pop()
    elif name == "changed_reset":
        value["after_resets"]["cases"][0]["readings"]["action"] += 1
    elif name == "changed_registered_verdict":
        value["frozen_report"]["verdicts"][0]["kind"] = "EQUIVALENT"
    elif name == "omitted_cuda_skip":
        value["frozen_report"]["verdicts"].pop()
    elif name == "changed_skip_reason":
        next(row for row in value["frozen_report"]["verdicts"] if row["kind"] == "SKIPPED")["detail"]["reason"] = "forged"
    elif name == "changed_source_binding":
        value["source_closure"]["E2"]["sha"] = SHAS["parent"]
    elif name == "changed_config_binding":
        value["causal"]["static"]["cpu-08"]["E2"]["ledger"]["config_inputs"]["environment.yaml"] = "forged"
    elif name == "changed_import_root":
        value["causal"]["static"]["cpu-08"]["E3"]["ledger"]["imported_source_root"] = "/tmp/forged"
    elif name == "changed_original_dirty_flag":
        value["frozen_report"]["meta"]["new_dirty"] = False
    else:
        raise ValueError("unknown required control")
    return value, allowance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spec_path = OUT / "proposed-spec.json"
    require(digest(spec_path) == args.spec_sha256, "unreviewed specification bytes")
    spec = read_json(spec_path)
    validate_bindings(spec)
    bank = bank_load()
    reading = compare_bank(bank, spec)
    controls = []
    for name in REQUIRED_CONTROLS:
        corrupt_bank, corrupt_spec = corrupt(name, bank, spec)
        try:
            compare_bank(corrupt_bank, corrupt_spec)
        except ValueError as error:
            controls.append({"name": name, "rejected": True, "reason": str(error)})
        else:
            raise AssertionError(f"required corruption control accepted: {name}")
    # Re-read all original bank, source and config bytes after private-copy controls.
    validate_bindings(spec)
    output = {
        "status": "separate scoped adjudication only; original literal commands remain FAILED",
        "spec_sha256": args.spec_sha256,
        "checker_sha256": spec["checker_sha256"],
        "reading": reading,
        "negative_controls": controls,
        "negative_controls_rejected": len(controls),
        "original_static_exit_remains_nonzero": True,
        "original_frozen_exit_remains_nonzero": True,
        "original_bank_source_config_bytes_unchanged": True,
        "cuda_qualified": False,
        "learning_or_convergence_qualified": False,
    }
    Path(args.output).write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"scoped_reading": reading, "negative_controls_rejected": len(controls), "original_gates_remain_failed": True}))


if __name__ == "__main__":
    main()
```
