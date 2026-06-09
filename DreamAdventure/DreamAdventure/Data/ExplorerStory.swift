import Foundation

// 海の探検家ストーリー：「うみの ひみつ」
// 動物：マリンイルカ 🐬
// テーマ：勇気・自然を大切にする心

extension StoryData {
    static var explorerStory: Story {
        let nodes: [String: StoryNode] = [

            // ── シーン1：海への憧れ（共感） ──
            "intro_1": StoryNode(
                id: "intro_1",
                scene: .opening,
                background: .beach,
                narration: [
                    "うみは ひろい。ひろくて、ふかくて、ふしぎ。",
                    "きみは まいにち うみを みながら おもった。",
                    "「うみの そこには なにが あるんだろう？」"
                ],
                characterDialogue: nil,
                interaction: .tapToContinue,
                nextNodeId: "intro_2",
                choices: []
            ),

            "intro_2": StoryNode(
                id: "intro_2",
                scene: .opening,
                background: .beach,
                narration: [
                    "ある あさはやく、なみうちぎわで ひかる ものを みつけた。",
                    "ちかづくと、それは… ちいさな イルカだった！",
                    "イルカは くるくる まわりながら きみに よびかけた。"
                ],
                characterDialogue: "「やあ！ ぼくは マリン。きみ、うみに きたいんでしょ？ たんけんに いこうよ！」",
                interaction: .tapCharacter,
                nextNodeId: "intro_3",
                choices: []
            ),

            "intro_3": StoryNode(
                id: "intro_3",
                scene: .opening,
                background: .ocean,
                narration: [
                    "マリンのせなかに つかまって、うみへとびこんだ！",
                    "あおい せかいが ひろがっていた。",
                    "カラフルな さかなたちが まわりを およいでいる。"
                ],
                characterDialogue: "「うわあ！ きれい！」",
                interaction: .tapToContinue,
                nextNodeId: "challenge_1",
                choices: []
            ),

            // ── シーン2：問題発生（挑戦） ──
            "challenge_1": StoryNode(
                id: "challenge_1",
                scene: .challenge,
                background: .ocean,
                narration: [
                    "とつぜん、そらが くらく なってきた。",
                    "おおきな なみが たちあがる。",
                    "あらしが やってきた！"
                ],
                characterDialogue: "「たいへん！ あらしだ！ ふかい ところに かくれなきゃ！」",
                interaction: .tapToContinue,
                nextNodeId: "challenge_2",
                choices: []
            ),

            "challenge_2": StoryNode(
                id: "challenge_2",
                scene: .challenge,
                background: .underwater,
                narration: [
                    "ふかい うみの そこで、きみたちは みつけた。",
                    "あみに からまった ちいさな たこ。",
                    "たこは こまって ないていた。"
                ],
                characterDialogue: "「マリン、こわいけど… あのたこを たすけたい。どうすれば いいかな？」",
                interaction: .choice,
                nextNodeId: nil,
                choices: [
                    StoryChoice(
                        id: "choice_afraid",
                        text: "こわいから にげる",
                        emoji: "😨",
                        nextNodeId: "choice_courage",
                        feedback: "マリンが ゆうきを くれた。"
                    ),
                    StoryChoice(
                        id: "choice_brave",
                        text: "ゆうきを だして たすける",
                        emoji: "✨",
                        nextNodeId: "cooperation_1",
                        feedback: "ゆうきって、こわくても やってみること！"
                    )
                ]
            ),

            "choice_courage": StoryNode(
                id: "choice_courage",
                scene: .challenge,
                background: .underwater,
                narration: [
                    "マリンが きみの よこに よりそった。"
                ],
                characterDialogue: "「ゆうきって、こわくない ことじゃないよ。こわいけど、それでも やってみること。ぼくも いっしょにいるから、だいじょうぶ。」",
                interaction: .tapCharacter,
                nextNodeId: "cooperation_1",
                choices: []
            ),

            // ── シーン3：協力して解決 ──
            "cooperation_1": StoryNode(
                id: "cooperation_1",
                scene: .cooperation,
                background: .underwater,
                narration: [
                    "きみは あみに てをのばした。",
                    "マリンが あみを くちばしで ほぐしてくれた。",
                    "ふたりで ちからを あわせると… あみが ゆるんだ！"
                ],
                characterDialogue: "「もうすこし！ がんばれ！」",
                interaction: .tapCharacter,
                nextNodeId: "cooperation_2",
                choices: []
            ),

            "cooperation_2": StoryNode(
                id: "cooperation_2",
                scene: .cooperation,
                background: .underwater,
                narration: [
                    "たこが じゆうに なった！",
                    "たこは おれいとして… しんかいの ほらあなへ あんないしてくれた。",
                    "そこには、きらきら ひかる たからものが！"
                ],
                characterDialogue: "「たすけてくれて ありがとう！ これ、うみの たから！」",
                interaction: .tapToContinue,
                nextNodeId: "achievement_1",
                choices: []
            ),

            // ── シーン4：夢の実現 ──
            "achievement_1": StoryNode(
                id: "achievement_1",
                scene: .achievement,
                background: .treasure,
                narration: [
                    "たからものの ほらあなは ひかりに あふれていた。",
                    "いろとりどりの さんご、ひかる いし、かわいい かいがら。",
                    "「これが うみの ひみつか…！」"
                ],
                characterDialogue: "「きみが ゆうきを だしたから、ここに これたんだよ。」",
                interaction: .tapToContinue,
                nextNodeId: "achievement_2",
                choices: []
            ),

            "achievement_2": StoryNode(
                id: "achievement_2",
                scene: .achievement,
                background: .ocean,
                narration: [
                    "あらしが すんで、うみは おだやかに なった。",
                    "きみは ほんとうの たんけんかに なった。",
                    "うみの いきものたちが みんな およいで まわった。"
                ],
                characterDialogue: "「きみは ほんもの の たんけんかだ！ うみの ことを だいじに してくれる ひとだから。」",
                interaction: .celebration,
                nextNodeId: "ending",
                choices: []
            ),

            "ending": StoryNode(
                id: "ending",
                scene: .ending,
                background: .beach,
                narration: [
                    "うみに かえって きた きみを、しおかぜが むかえた。",
                    "てのひらには、マリンから もらった ちいさな かいがら。",
                    "「ゆうきを だせば、あたらしい せかいが ひらく。」"
                ],
                characterDialogue: "「またいつでも あそびに きてね！ うみは いつも ここにいるよ！」",
                interaction: .celebration,
                nextNodeId: nil,
                choices: []
            )
        ]

        return Story(
            dreamType: .explorer,
            nodes: nodes,
            startNodeId: "intro_1"
        )
    }
}
