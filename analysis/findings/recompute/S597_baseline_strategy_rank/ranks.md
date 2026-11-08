<!-- provenance
{
 "script": "scripts/S597_baseline_strategy_rank.py",
 "script_sha256": "812e43e7eddc7217e8f605c9edc3878f48c9d500e1e7ce286b9392898a38f9f0",
 "command": "uv run --frozen python scripts/S597_baseline_strategy_rank.py",
 "imported": {
  "scripts/S497_fig5_d166.py": {
   "sha256": "191495f5b8a88ed2d2ec10f18e1296a7e8c33aed8deb47c297bdb9ee2bbc42c0",
   "equals_head": true
  },
  "scripts/S540_fig5_evaluators.py": {
   "sha256": "f794d4e6e40179894d22905220e79daa42693710c3f6ba4c10ee09c5b7297c77",
   "equals_head": true
  },
  "scripts/S542_supp_evaluators.py": {
   "sha256": "f86c5189afe2d38da3283946e08acbf12aa3e1e10ad266321ec3fc82f283c1b1",
   "equals_head": true
  },
  "scripts/S473_fig5_panels.py": {
   "sha256": "14fb59be3a4e3e405d38f7c2b772acc3ac62ee88cabc6aa171a8a7124a90d49a",
   "equals_head": true
  }
 },
 "checked_against": {
  "findings/figures_provisional/fig5/figure5_numbers.json": "7fefdfcb5549fadc29da08ebd48bc7f69b1c6d9716632a398f97933a6c6a145f",
  "findings/figures_provisional/supp_fig18_evaluators/supplementary_figure18_numbers.json": "78d0df96e167ecd29c9795a62df8415bf1e8dd18f96abf26e6dc4e2bb94ca655"
 },
 "inputs_sha256": {
  "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/MANIFEST.sha256": "60c1f703d7b5853ec7bd5aebaecec9ac50ea3cb078b1f44741c5964427635b2e",
  "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/runs/exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl": "ecb6de5343d172894fd56d57997e3301d70ca3fb509ae2cd65f8e47eb8c268b7",
  "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/runs/exp_01__rlm_20__exp_v4_s20_n0/answers.jsonl": "1e5b124d8bbd98640c87051916305ed0c04d668447967c60a08d6945fca32c62",
  "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/runs/exp_01__rlm_5__exp_v4_s20_n0/answers.jsonl": "cc10c9eb881fa9618ff2fb8ec7a3f1bb9cf58662827cd67b326e47f67b51d42c",
  "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/runs/exp_01__verified_pass__exp_v4_s20_n0/answers.jsonl": "1ce4b1052912d8592b912da29ed987df9c2a4baca575cf80cc2b9d33334f8148",
  "fig2_inputs/g1_collect.jsonl": "f5ff75bc244cda492a48e7e11f54f2007ed7d586a8f49e78921edd7244b28965",
  "fig2_inputs/out/judge/exp_01__multi_hop__exp_v4_s20_n0/judge_passages.jsonl": "26d6f9763894f7681748ba36edf8db1f66e8e0dbbf6c16459815c4a5a01bff02",
  "fig2_inputs/out/judge/exp_01__multi_hop__exp_v4_s20_n0/judge_passages_headers.jsonl": "07fc15236e5acd765f3b02cd13d7886678fa96d13a3c11e268453e6cbda1d53e",
  "fig2_inputs/out/judge/exp_01__multi_hop__exp_v4_s20_n0/judge_passages_recheck.jsonl": "4df3fbd809f9397d9e3a9364b737696a9fa42ac42d6526859f512c6e9c57adf4",
  "fig2_inputs/out/judge/exp_01__rlm_10__exp_v4_s20_n0/judge_passages.jsonl": "7f72e416ae15f93bc68704710ae1f8832d3c47c5fa6d1375911063ae8faa6903",
  "fig2_inputs/out/judge/exp_01__rlm_10__exp_v4_s20_n0/judge_passages_headers.jsonl": "5fbc1e2c694ec542ae03f5f43ced98be8c2b2b507219407d980d5c411ce89fa3",
  "fig2_inputs/out/judge/exp_01__rlm_10__exp_v4_s20_n0/judge_passages_recheck.jsonl": "57586f90f6f3834edc1749883c1f2c7c4aa1f2c64febc4c3e069e4fa1d49ed1c",
  "fig2_inputs/out/judge/exp_01__rlm_20__exp_v4_s20_n0/judge_passages.jsonl": "98b097115b456b546b42ab7ec65d4c22cc0291ce85871caae7cc41df8d697de4",
  "fig2_inputs/out/judge/exp_01__rlm_20__exp_v4_s20_n0/judge_passages_headers.jsonl": "df3950357a14d650ecce6dd0fcf04631133b82598502593e722e39cb00d031e1",
  "fig2_inputs/out/judge/exp_01__rlm_20__exp_v4_s20_n0/judge_passages_recheck.jsonl": "28c3ced011c59b2be79383998e12575c758e87d5f7f7747e79345ef677b0d561",
  "fig2_inputs/out/judge/exp_01__rlm_5__exp_v4_s20_n0/judge_passages.jsonl": "6025d3d2b72de28f5c4dcdf15399dc4c09f3b8ddbf10dc9dfa032b46f4eb4ee4",
  "fig2_inputs/out/judge/exp_01__rlm_5__exp_v4_s20_n0/judge_passages_headers.jsonl": "bf4d3864c82fe7527d98dfec1104524346db81e60665e34752257916a22162d6",
  "fig2_inputs/out/judge/exp_01__rlm_5__exp_v4_s20_n0/judge_passages_recheck.jsonl": "7b85db45a29598004357f5f782a0865a882b994ca39497831a5b7cb494c28c3c",
  "fig2_inputs/out/judge/exp_01__single_pass__exp_v4_s20_n0/judge_passages.jsonl": "71d15cc7f2837f508bb5d6e7b8fe6da0c09dc270f527e90fa0dfd9a22606754c",
  "fig2_inputs/out/judge/exp_01__single_pass__exp_v4_s20_n0/judge_passages_headers.jsonl": "c440945a8f4a7935a723bfee2696311c929af25b77a3f9c168c10be8708bf5a7",
  "fig2_inputs/out/judge/exp_01__single_pass__exp_v4_s20_n0/judge_passages_recheck.jsonl": "6e87f813328dc148ca75d5a6edcfa3c0f5c8d91d09c9dbb22e11849fdba282c1",
  "fig2_inputs/out/judge/exp_01__verified_pass__exp_v4_s20_n0/judge_passages.jsonl": "500ddd46b2f7f09fe10e9358f06df56a762908ab63f74bba9db5af0ce43602cf",
  "fig2_inputs/out/judge/exp_01__verified_pass__exp_v4_s20_n0/judge_passages_headers.jsonl": "e54367e51670704bf004ff801c92186d4917d828cc06343499d060dc0515f3af",
  "fig2_inputs/out/judge/exp_01__verified_pass__exp_v4_s20_n0/judge_passages_recheck.jsonl": "1d47d790fa987efac2e6130e64b0a0e6319c2006f51af614646ae542bbc0781c",
  "fig2_inputs/out/start_11455_20261018T120423.json": "8a68e8be636cd95627ff3cedc6e90463b24bbcb537f13a8335c4b6638fc9852a",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_10__exp_v4_s20_n0/judge_passages.jsonl": "110c1e9c09248afb037eb45a50de5c5007e246ecee15225e55d1d51354d5211b",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_10__exp_v4_s20_n0/judge_passages_headers.jsonl": "ab538fd7b0c60f5602e03d1048a1249ad866048b852ae372d2e3d2e592665f02",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_10__exp_v4_s20_n0/judge_passages_recheck.jsonl": "bd0fdd77cfdf1784f626e1fa38e7ca4e03315e26a08559a0671b5f4792f652ff",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_20__exp_v4_s20_n0/judge_passages.jsonl": "5cb96e389c9d40027b252ac841d3eabcd839dda0000a14944eaafe33db0afcb8",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_20__exp_v4_s20_n0/judge_passages_headers.jsonl": "a0475ebc7d8b2fa225e0292de706d676649870848f25dcbc90976f5f1a44f4c2",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_20__exp_v4_s20_n0/judge_passages_recheck.jsonl": "98e26491c4be27808286fcbd877bf5655fa702e8e5872a5eadfdc0b55487e7d2",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_5__exp_v4_s20_n0/judge_passages.jsonl": "acd6e982d4e0ee95f5ec4291376065bfb250f3535c110be0dfaabd9a1cadf64b",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_5__exp_v4_s20_n0/judge_passages_headers.jsonl": "86eaa691b55ff49b58650de018ba4fac6181cb9fd36da6041d17723b23e38df8",
  "fig2_inputs/out_g1r15/judge/exp_01__rlm_5__exp_v4_s20_n0/judge_passages_recheck.jsonl": "ae7447bbd85bc4091b8cd003429443e36926babc530bb27d44a7edf11dca00b8",
  "fig2_inputs/out_g1r15/judge/exp_01__verified_pass__exp_v4_s20_n0/judge_passages.jsonl": "7cf78a8fe562b49b4c4181e7ed496528ecdb56f4ed697e71eeec64ef9f0bd3b3",
  "fig2_inputs/out_g1r15/judge/exp_01__verified_pass__exp_v4_s20_n0/judge_passages_headers.jsonl": "810ad439b7a1fd3b3bf2a571001b7701c4c768746fde77a07e1af5ec8530e423",
  "fig2_inputs/out_g1r15/start_11455_20261018T120423.json": "8a68e8be636cd95627ff3cedc6e90463b24bbcb537f13a8335c4b6638fc9852a",
  "fig5_1028_inputs/PULL.json": "411b6109ef3cbc3acd1c30b5cfa18513a9d9c4ecaaa963f446b5864646cfe072",
  "fig5_1028_inputs/anchor_d166/Figure 5 (provisional, assembled 28 Oct).png": "615b7f5486978f0a5b42cb85767d0a13528e79080942d67e54d244f354e0a067",
  "fig5_1028_inputs/anchor_d166/figure5_numbers.json": "2df54409d6b8823bc088945f139a6baaf1f2af5e0c9395ef445fe0ca866ac8d1",
  "fig5_1028_inputs/anchor_d166/legend.md": "c01b848260d3b6c52ce97da3ff4fbccbfec887afb4339313722442c6679ee10b",
  "fig5_1028_inputs/anchor_d166/numbers.json": "d653a0086af7bda805be8acd17afc85187f37b17485c4d37985502e678d129d5",
  "fig5_1028_inputs/l1/READ_LOG.json": "999d8755baa378cd0c025426eabc256535f8d487f0b34af2ffd0cb0e0ffb9cb3",
  "fig5_1028_inputs/l1/header.json": "1a747b183049f9f85f3092b1f61ccb6b80a45346b0a36a3c37d666ea81b98f41",
  "fig5_1028_inputs/l1/key/key.shard0of1.jsonl": "5157ce1f2e11b9e90970c79af17dbc3138579f03d7fde9ea0611e416278b74ce",
  "fig5_1028_inputs/l1/overlap/overlap.shard0of1.jsonl": "277bbfe9e65d0917febba6d06365803dbd10c411376fa64322cad4bae536ddd3",
  "fig5_1028_inputs/l1/papers/papers.shard0of25.jsonl": "a72473858e2b0cbe5fbb651afd30fa20c135cccc506313339185cfb8f579469e",
  "fig5_1028_inputs/l1/papers/papers.shard0of3.jsonl": "497119e9aacccf795455cd0666a88fed141750f74805e28dd4ebe4eca27a776d",
  "fig5_1028_inputs/l1/papers/papers.shard0of6.jsonl": "02a128b0c628f1fe2dc5d6e2488c8bf6aeeb46f470e6a8047e97b71c5191705e",
  "fig5_1028_inputs/l1/papers/papers.shard0of8.jsonl": "3bc371e114a18ae860ffcdfd46bb571d4ac9cb406a609adbae13d05c9e763d94",
  "fig5_1028_inputs/l1/papers/papers.shard11of25.jsonl": "24124256d4eeb63160a3de3822cb23cf5db52a2303945a384b439e23255d8b7c",
  "fig5_1028_inputs/l1/papers/papers.shard17of25.jsonl": "c183ec0074924e3ac79866525cbca5a64de3dfb5ce5459813d6e5296e1f98fda",
  "fig5_1028_inputs/l1/papers/papers.shard1of3.jsonl": "20cb43f9b64ed071e4b1d9dd93669289bb7c908922cb963d1c0113943057d915",
  "fig5_1028_inputs/l1/papers/papers.shard1of6.jsonl": "a340682c9ea14b08de5934c22879afba9a836d7a80dfd8ec62cf88f23c9e5af5",
  "fig5_1028_inputs/l1/papers/papers.shard1of8.jsonl": "893cce2612d5417494f074c38cc1ed5153eefa162f02b8947e425dca7bcb92ab",
  "fig5_1028_inputs/l1/papers/papers.shard21of25.jsonl": "a0b9b54c1e2c9e173bda8ee55fda11444e29b897501372deb35348715286ba95",
  "fig5_1028_inputs/l1/papers/papers.shard23of25.jsonl": "44bc7352c7cdcfefeaa924981f78fcf0be6f32ba3a12494c528159814ce39b66",
  "fig5_1028_inputs/l1/papers/papers.shard24of25.jsonl": "3cc090aaed37913d2a6518557ca48ab0a09dd3ff02bbfea594246eb71d0ecb1d",
  "fig5_1028_inputs/l1/papers/papers.shard2of3.jsonl": "fd6ced90b95846cf0cb7004a8b9edc805c6791202b75c499912ab5e76dc1f9b2",
  "fig5_1028_inputs/l1/papers/papers.shard2of6.jsonl": "7e2c5259192e0344ca3f4a9f8badd2bf895422acf470bdb506365ab46e485186",
  "fig5_1028_inputs/l1/papers/papers.shard2of8.jsonl": "a1838a9662038cef7e16f510081c40e2476e5347caba34af7bab0aa02a0ea97c",
  "fig5_1028_inputs/l1/papers/papers.shard3of25.jsonl": "1801f791b1ae7c0bd2fc0a581d339bcc954616b41621a7c72df9b22e0f1e4f8f",
  "fig5_1028_inputs/l1/papers/papers.shard3of6.jsonl": "e9d3026b2aaac173fbc9120ea0548ec71c3750555e6e79ce7b2e9ad1c571e79f",
  "fig5_1028_inputs/l1/papers/papers.shard4of25.jsonl": "1d1a91cd52264524d7b2171c427495ad734e15741877e38507e2e0ff3777eb1e",
  "fig5_1028_inputs/l1/papers/papers.shard4of6.jsonl": "0cf00913ee8f25d6447785b67ac98e280aa7ccaeabc02ac51fad51e6fcbcf598",
  "fig5_1028_inputs/l1/papers/papers.shard4of8.jsonl": "64df74e6a50527d223906cfb9fb5bd393871de91a2c11816f5953ac44d24d15e",
  "fig5_1028_inputs/l1/papers/papers.shard5of6.jsonl": "0ab765f577e1ce718f31eb923632b032ac5b23b7c28fc68f3fecf965878672c4",
  "fig5_1028_inputs/l1/papers/papers.shard6of8.jsonl": "3cd4eb94c8ba1af3756e65e535bc83c425d6b6c8ad9595c8ead15f5ab59384b8",
  "fig5_1028_inputs/l1/papers/papers.shard9of25.jsonl": "4c07787970aa66c359f4ea0768b874c7ceb9c5585c9ef7b6760ab8c59872bf7c",
  "fig5_1028_inputs/s3/IDENTICAL_FILES.tsv": "a7b94e33e9c877bd2828539c3539b818908377060f34c28c68d0c8332c9b3fe6",
  "fig5_1028_inputs/s3/g1_collect.jsonl.json": "a3f8bb0ef68c92af5e8d0de46396aab407973953da02f6abd8c766be95df126a",
  "fig5_d200_inputs/PULL.json": "e040c376630f10a4f19a8abbb3d82fe9194fe294e9af7d2b2bb3431af2dd274c",
  "fig5_d200_inputs/k1/amendments.json": "9eb74535f1ef2f6d353f7da9937c903b5c4495a24c7b71a01aa859f8beb62593",
  "fig5_d200_inputs/k1/assignment.json": "dba7744869ac8ce1fee2a75d2e0eed009dbc6514e8e1048aa3c0b58db0e014a3",
  "fig5_d200_inputs/k1/beelink/READ_LOG.json": "d986ad2c7af5db9657c68d93e90d465382addce1b250e29e3a0a8933749d68d3",
  "fig5_d200_inputs/k1/beelink/ragas/ragas.jsonl": "0e638d3df15915b43569c6ccd83c977a8e2bdc050079973138c9094d0c1c24d1",
  "fig5_d200_inputs/k1/beelink/ragas/ragas_headers.jsonl": "d3afe9580caefb0eacd94f0af4d02d6636baff65fd996d1961a93ab597002d38",
  "fig5_d200_inputs/k1/beelink/ragchecker/ragchecker.jsonl": "e0ba5d5a77de8683a0f9b0da320322bb731d1decebcc3cc676b6873e4a0a0804",
  "fig5_d200_inputs/k1/beelink/ragchecker/ragchecker_headers.jsonl": "198afeffba587b7842deb8323dddb6430f7b114eb066fce3158ca910d59a9734",
  "fig5_d200_inputs/k1/beelink_112/READ_LOG.json": "bd6fb6fa100be44a8d06a535afa6bce597ba3b6d1c38959e640d0e5e4ef84e03",
  "fig5_d200_inputs/k1/beelink_112/ragas/ragas.jsonl": "2996a96369fb7864d6a21b68fde310bbbbf0698f8e605ad26595ab6017b8bfc1",
  "fig5_d200_inputs/k1/beelink_112/ragas/ragas_headers.jsonl": "0aab48caa8d1373d3e2b3aa1cdf3705b91e5cc775a915090c4df9fd0bd075113",
  "fig5_d200_inputs/k1/beelink_112/ragchecker/ragchecker.jsonl": "a61432fbd62eb81cc7d671d011c66c1241773b8b77898f6ee15b48251418f5e5",
  "fig5_d200_inputs/k1/beelink_112/ragchecker/ragchecker_headers.jsonl": "85ce9e46cb3856984ece339662fe04fabf11bd10b5b1cda32699a9eff99f90ba",
  "fig5_d200_inputs/k1/beelink_11435/READ_LOG.json": "40b4fb59a54a898e82c0465ea5055b89819fc86bca2c4641edeb0b5e3cf97edf",
  "fig5_d200_inputs/k1/beelink_11435/ragas/ragas.jsonl": "9ea23ba9b6328998670d70197250717e63413603d42df0154e05ec34f3541a96",
  "fig5_d200_inputs/k1/beelink_11435/ragas/ragas_headers.jsonl": "db55a8f0020f662f7e61082e272b7c9002ca576069cf1fa4a7eae7fe59a3ce7a",
  "fig5_d200_inputs/k1/beelink_11435/ragchecker/ragchecker.jsonl": "51ee403df907ed532a4f3349eb14440ef1cb3510f7c5addde3e6765bb41e20e2",
  "fig5_d200_inputs/k1/beelink_11435/ragchecker/ragchecker_headers.jsonl": "c2cb991f8e9b722f72ce3a15f3e6f8f1128c735f9fb21240a9c01af75640c00f",
  "fig5_d200_inputs/k1/laptop/READ_LOG.json": "6c081e940429e2e6c8b138cad74b4b638f5656193f0d8e0f28e085bbd39ec891",
  "fig5_d200_inputs/k1/laptop/ragas/ragas.jsonl": "81be5a14131ee338bec56a8178ebd250943371a2fe4383a359e9555528e56800",
  "fig5_d200_inputs/k1/laptop/ragas/ragas_headers.jsonl": "e3d5779e627267587c70d4cd28cff076d3842f7721c5327ceb69fcd8c3dd6250",
  "fig5_d200_inputs/k1/laptop/ragchecker/ragchecker.jsonl": "af3d8874590559c18a54cd5329c09e06342942127ed99d2e2edd0a0be2937734",
  "fig5_d200_inputs/k1/laptop/ragchecker/ragchecker_headers.jsonl": "c134ee2c0a13e18ab30aa084146dde8e2b3a1e457298368eb51954b0a882e85a",
  "fig5_d200_inputs/k1/studio/READ_LOG.json": "870bc1f0cf0164a01fe14fb67757398f07f468f32460d5144bf90bacc9bbbdd3",
  "fig5_d200_inputs/k1/studio/ragas/ragas.jsonl": "f268e97edff02ae63d1087672df6dcfff3ca91d79819266e1392157716009686",
  "fig5_d200_inputs/k1/studio/ragas/ragas_headers.jsonl": "0bc224e0787b6cf9278b1f824a1aaf468e0ee5107e100c73d905408c60bcf0f5",
  "fig5_d200_inputs/k1/studio/ragchecker/ragchecker.jsonl": "7ea25498da0e6f4e9d5e2f3843bfc470862ea15933d43a7668ec78b83cdd2669",
  "fig5_d200_inputs/k1/studio/ragchecker/ragchecker_headers.jsonl": "854c6a1f39cb2cd2be78f9669c06ff52d9cd8a261b6d0191dd45772204b00f7e",
  "fig5_d200_inputs/k1/studio_11451/READ_LOG.json": "3a2568ecaf9838fc700cab6a25fc31aaed65f9d192cb24fc2c3bd83774800bf5",
  "fig5_d200_inputs/k1/studio_11451/ragas/ragas.jsonl": "283a4394e46541cf308952e02e26d2c016dc5f4be037b9e1523625aeb0fc504f",
  "fig5_d200_inputs/k1/studio_11451/ragas/ragas_headers.jsonl": "a6d8252e3e18a72b3e93db51d8142e205f761664fd6a32a3721628eacb628c06",
  "fig5_d200_inputs/k1/studio_11451/ragchecker/ragchecker.jsonl": "17312beb92c5723db0d87223de06479a106672b3fa8920335366695987434ad5",
  "fig5_d200_inputs/k1/studio_11451/ragchecker/ragchecker_headers.jsonl": "c5df0905d23954e617434e4f5a2934d91ec345c63da34e6f5507c539e30a74fa",
  "fig5_d200_inputs/k1/studio_11456/READ_LOG.json": "edfb886829b028325d0c0ddbd79a82515d3dc1f86a0eb0b6e70e5ba69c2f69e2",
  "fig5_d200_inputs/k1/studio_11456/ragas/ragas.jsonl": "3a39873c12429799b7e87e2c004dcbfb86ce429c58ff34dbdeebbb18f4c05fa1",
  "fig5_d200_inputs/k1/studio_11456/ragas/ragas_headers.jsonl": "abecf46ebe69682eccf0697a5ab854e5f84d53438d033bbb9fbcb6ce20e022ac",
  "fig5_d200_inputs/k1/studio_11456/ragchecker/ragchecker.jsonl": "f9a90b7e134bd692dc39a298497f83eb98470ab1d716c4dd313f53edd85f9fc8",
  "fig5_d200_inputs/k1/studio_11456/ragchecker/ragchecker_headers.jsonl": "83eead5c97be90fb5af900dea4e56b734a2b718c99424f7e95ce9039ab35b3be",
  "fig5_d200_inputs/l1/READ_LOG.json": "5dd7f42a4fedd08ef41aa95aa215a98e73c45b85c023b1d0d5ebdd699058f7b1",
  "fig5_d200_inputs/l1/header.json": "1a747b183049f9f85f3092b1f61ccb6b80a45346b0a36a3c37d666ea81b98f41",
  "fig5_d200_inputs/l1/key/key.shard0of1.jsonl": "5157ce1f2e11b9e90970c79af17dbc3138579f03d7fde9ea0611e416278b74ce",
  "fig5_d200_inputs/l1/overlap/overlap.shard0of1.jsonl": "277bbfe9e65d0917febba6d06365803dbd10c411376fa64322cad4bae536ddd3",
  "fig5_d200_inputs/l1/papers/papers.shard0of25.jsonl": "a72473858e2b0cbe5fbb651afd30fa20c135cccc506313339185cfb8f579469e",
  "fig5_d200_inputs/l1/papers/papers.shard0of3.jsonl": "497119e9aacccf795455cd0666a88fed141750f74805e28dd4ebe4eca27a776d",
  "fig5_d200_inputs/l1/papers/papers.shard0of6.jsonl": "02a128b0c628f1fe2dc5d6e2488c8bf6aeeb46f470e6a8047e97b71c5191705e",
  "fig5_d200_inputs/l1/papers/papers.shard0of8.jsonl": "3bc371e114a18ae860ffcdfd46bb571d4ac9cb406a609adbae13d05c9e763d94",
  "fig5_d200_inputs/l1/papers/papers.shard11of25.jsonl": "24124256d4eeb63160a3de3822cb23cf5db52a2303945a384b439e23255d8b7c",
  "fig5_d200_inputs/l1/papers/papers.shard17of25.jsonl": "c183ec0074924e3ac79866525cbca5a64de3dfb5ce5459813d6e5296e1f98fda",
  "fig5_d200_inputs/l1/papers/papers.shard1of3.jsonl": "20cb43f9b64ed071e4b1d9dd93669289bb7c908922cb963d1c0113943057d915",
  "fig5_d200_inputs/l1/papers/papers.shard1of6.jsonl": "a340682c9ea14b08de5934c22879afba9a836d7a80dfd8ec62cf88f23c9e5af5",
  "fig5_d200_inputs/l1/papers/papers.shard1of8.jsonl": "893cce2612d5417494f074c38cc1ed5153eefa162f02b8947e425dca7bcb92ab",
  "fig5_d200_inputs/l1/papers/papers.shard21of25.jsonl": "a0b9b54c1e2c9e173bda8ee55fda11444e29b897501372deb35348715286ba95",
  "fig5_d200_inputs/l1/papers/papers.shard23of25.jsonl": "44bc7352c7cdcfefeaa924981f78fcf0be6f32ba3a12494c528159814ce39b66",
  "fig5_d200_inputs/l1/papers/papers.shard24of25.jsonl": "06fce15507c7a59000a8757f5ee30435e4ec604e9c70d0e15443a9285d2b0457",
  "fig5_d200_inputs/l1/papers/papers.shard2of3.jsonl": "fd6ced90b95846cf0cb7004a8b9edc805c6791202b75c499912ab5e76dc1f9b2",
  "fig5_d200_inputs/l1/papers/papers.shard2of6.jsonl": "7e2c5259192e0344ca3f4a9f8badd2bf895422acf470bdb506365ab46e485186",
  "fig5_d200_inputs/l1/papers/papers.shard2of8.jsonl": "a1838a9662038cef7e16f510081c40e2476e5347caba34af7bab0aa02a0ea97c",
  "fig5_d200_inputs/l1/papers/papers.shard3of25.jsonl": "b54035daba5b91c5342079b8564e0c083a4d6cce8485b8e619974938672a601f",
  "fig5_d200_inputs/l1/papers/papers.shard3of6.jsonl": "e9d3026b2aaac173fbc9120ea0548ec71c3750555e6e79ce7b2e9ad1c571e79f",
  "fig5_d200_inputs/l1/papers/papers.shard4of25.jsonl": "1d1a91cd52264524d7b2171c427495ad734e15741877e38507e2e0ff3777eb1e",
  "fig5_d200_inputs/l1/papers/papers.shard4of6.jsonl": "0cf00913ee8f25d6447785b67ac98e280aa7ccaeabc02ac51fad51e6fcbcf598",
  "fig5_d200_inputs/l1/papers/papers.shard4of8.jsonl": "64df74e6a50527d223906cfb9fb5bd393871de91a2c11816f5953ac44d24d15e",
  "fig5_d200_inputs/l1/papers/papers.shard5of6.jsonl": "0ab765f577e1ce718f31eb923632b032ac5b23b7c28fc68f3fecf965878672c4",
  "fig5_d200_inputs/l1/papers/papers.shard6of8.jsonl": "3cd4eb94c8ba1af3756e65e535bc83c425d6b6c8ad9595c8ead15f5ab59384b8",
  "fig5_d200_inputs/l1/papers/papers.shard9of25.jsonl": "e240a252336f3b9e7008c5484a9777ae513979ecfd0b49d127f94a23e5179c75",
  "findings/recompute/G1_runs/rerun_d89.sh": "8549210c7e829229ba83b0dd5afcc804454cda00aed665ce586ede5e24d98260",
  "findings/recompute/L3/concept_recall.jsonl": "56f0f23b3415169a2ec5a79f6fb9cbf427939054279b9ebc32b21cf07c6e2f36",
  "findings/recompute/L3/header.json": "01597d0c39704f1e1abfa132231eee57a9a839b111340ea0b5a85b2482bf0b5f",
  "findings/recompute/S26_signal_redundancy.json": "07dd836183ddedda293f203488058a1ab31101bafd821e4ba012a2e19f218951",
  "findings/recompute/S30_baseline_scores_full.csv": "6bfb240e74fae89d713279227eed9eff529262819ff5a2492cd17de0ac713256",
  "findings/recompute/S564_claimify_selection/full/shard_0_of_8/rows.jsonl": "625c826c7d9754fdf4138706a473be0c1db2a27cfac6b81e24119d6ed24957e2",
  "findings/recompute/S564_claimify_selection/full/shard_1_of_8/rows.jsonl": "9d16d8ef2e3728cf4a1ee7496533137b52b81ba378b49879a6261a9fc97a51c8",
  "findings/recompute/S564_claimify_selection/full/shard_2_of_8/rows.jsonl": "c468afe65bf3ec2e8f1d3378f6c4c25e76bf0c843c1f4abb5457541e56ea8a1e",
  "findings/recompute/S564_claimify_selection/full/shard_3_of_8/rows.jsonl": "285557e2076d4929b9884d357c77d06a837f12ff4ad04ab899697f202fab346c",
  "findings/recompute/S564_claimify_selection/full/shard_4_of_8/rows.jsonl": "02836c18e7beb0e153cadd155e426e300a6ff64616084cd6539c6d2bfd18d8a2",
  "findings/recompute/S564_claimify_selection/full/shard_5_of_8/rows.jsonl": "98aa0c9a01228b529822db4afb417ff2d089e0a57ad5858723aa329d1d381143",
  "findings/recompute/S564_claimify_selection/full/shard_6_of_8/rows.jsonl": "c2207de96ab259dfe75f845250f4854fe1f8c76a1f20ce7c93e0a3c9fe96bd9d",
  "findings/recompute/S564_claimify_selection/full/shard_7_of_8/rows.jsonl": "d79480616e40d3ffa7c7043eb7ab62ab88fbea9ce4ecb63061e7137af8b66eb0",
  "k1_inputs_runs.tar:k1_inputs_runs/exp_01__multi_hop__exp_v4_s20_n0/answers.jsonl": "518b0efefd170ec4e172b8ba1d8218aa25612a4eaf27ebab98a824343864ad42",
  "k1_inputs_runs.tar:k1_inputs_runs/exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl": "7d5d2651b0111d96cc863af5a5e9349d07466d6028be2407c1644ef31e7ab90b",
  "k1_inputs_runs.tar:k1_inputs_runs/exp_01__rlm_20__exp_v4_s20_n0/answers.jsonl": "18ba730cee1865455aa5ce7481ffdb205271791a35d67a71a222819f924e27dc",
  "k1_inputs_runs.tar:k1_inputs_runs/exp_01__rlm_5__exp_v4_s20_n0/answers.jsonl": "fa8a221fd22f11e516d8204116a8a25b51e4eabe654615d16516456373276b81",
  "k1_inputs_runs.tar:k1_inputs_runs/exp_01__single_pass__exp_v4_s20_n0/answers.jsonl": "bc43f45f211b64ad625db677110d6346dfd6d5bdda9387a6647d0d957cc5dccd",
  "k1_inputs_runs.tar:k1_inputs_runs/exp_01__verified_pass__exp_v4_s20_n0/answers.jsonl": "8489392b4723a8d4fa8bd3727e83853256d8d68d30e7d44c8d81bbf4beb2e6b7"
 },
 "model_calls": 0
}
-->

# S597: the six strategies ranked by each baseline evaluator (BASELINE-RANK, O1)

Draw 1, answerable questions, 75 questions on which all six answers carry the judge's score and every score below (S542.rank_rows's method). Rank 1 is the highest mean. order_rho: Spearman's rho of the row's six ranks with the row 'judge, 4 or more'; order_rho_5c: with the judge's ranks printed in Figure 5 c (three draws, 86 questions). No interval: six items.

Reproduced first:

- (1) Spearman's rho with the judge's correctness and its n equal sheet Fig. 5e on 10 rows
- (2) S542.rank_rows equals Supplementary Fig. 18b: 20 rows x 6 strategies, 75 questions
- (3) Fig. 5c's judge ranks: single pass 1, multi-hop 3, verified pass 2, RLM-5 4, RLM-10 5, RLM-20 6

| family | row | single pass | multi-hop | verified pass | RLM-5 | RLM-10 | RLM-20 | order_rho | order_rho_5c |
|---|---|---|---|---|---|---|---|---|---|
| judge | judge, 4 or more | 2 (0.867) | 3 (0.813) | 1 (0.893) | 5 (0.747) | 4 (0.760) | 6 (0.720) | 1.000 | 0.886 |
| judge | judge, 3 or more | 1 (0.973) | 2 (0.960) | 4 (0.947) | 4 (0.947) | 4 (0.947) | 6 (0.933) | 0.638 | 0.820 |
| signal | Concepts | 5 (0.740) | 6 (0.558) | 4 (0.742) | 2 (0.775) | 1 (0.797) | 3 (0.755) | -0.543 | -0.657 |
| signal | Papers | 2 (0.807) | 6 (0.581) | 1 (0.832) | 4 (0.707) | 3 (0.732) | 5 (0.688) | 0.657 | 0.543 |
| RAGAS | RAGAS faithfulness | 1 (0.971) | 3 (0.882) | 2 (0.949) | 5 (0.840) | 6 (0.834) | 4 (0.849) | 0.714 | 0.829 |
| RAGAS | RAGAS factual correctness | 2 (0.584) | 3 (0.509) | 1 (0.594) | 5 (0.438) | 4 (0.463) | 6 (0.419) | 1.000 | 0.886 |
| RAGChecker | RAGChecker faithfulness | 2 (0.788) | 3 (0.713) | 1 (0.815) | 5 (0.667) | 4 (0.676) | 6 (0.666) | 1.000 | 0.886 |
| RAGChecker | RAGChecker F1 | 2 (0.508) | 3 (0.458) | 1 (0.523) | 5 (0.395) | 4 (0.399) | 6 (0.380) | 1.000 | 0.886 |
| simple | ROUGE-L | 2 (0.280) | 3 (0.254) | 1 (0.291) | 5 (0.134) | 4 (0.135) | 6 (0.131) | 1.000 | 0.886 |
| simple | METEOR | 1 (0.388) | 6 (0.275) | 2 (0.385) | 4 (0.309) | 3 (0.316) | 5 (0.305) | 0.600 | 0.600 |
| simple | Number overlap | 5 (0.519) | 6 (0.459) | 4 (0.520) | 3 (0.683) | 1 (0.713) | 2 (0.696) | -0.600 | -0.771 |
| simple | bge-m3 similarity | 2 (0.844) | 3 (0.824) | 1 (0.847) | 6 (0.784) | 4 (0.790) | 5 (0.787) | 0.943 | 0.771 |

Each cell: rank (mean).

## The sentence for the letter (Reviewer 1, Comment 1.5)

On the 75 questions where all six answers carry every score, 7 of the 8 evaluators ranked the strategies in the judge's direction (Spearman's rho 0.60 to 1.00 against the judge's order). Number overlap ranked them against it (rho −0.60).
