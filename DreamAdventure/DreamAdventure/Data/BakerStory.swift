import Foundation

// ケーキ職人ストーリー：「まほうの ケーキ」
// 動物：シェフうさぎ 🐰
// テーマ：やさしさ・みんなを笑顔にする喜び

extension StoryData {
    static var bakerStory: Story {
        let nodes: [String: StoryNode] = [

            // ── シーン1：ケーキへのあこがれ（共感） ──
            "intro_1": StoryNode(
                id: "intro_1",
                scene: .opening,
                background: .bakery,
                narration: [
                    "まちの かどに すてきな おかし やさんが あった。",
                    "まいにち あまい においが まちじゅうに ひろがる。",
                    "「いつか ぼく（わたし）も、みんなを えがおに する ケーキを つくりたい！」"
                ],
                characterDialogue: nil,
                interaction: .tapToContinue,
                nextNodeId: "intro_2",
                choices: []
            ),

            "intro_2": StoryNode(
                id: "intro_2",
                scene: .opening,
                background: .kitchen,
                narration: [
                    "きょうは はじめて じぶんで ケーキを つくる ひ！",
                    "でも よういした ざいりょうを みると…",
                    "たまごが たりない！ こむぎこも たりない！"
                ],
                characterDialogue: nil,
                interaction: .tapToContinue,
                nextNodeId: "intro_3",
                choices: []
            ),

            "intro_3": StoryNode(
                id: "intro_3",
                scene: .opening,
                background: .kitchen,
                narration: [
                    "そのとき、まどから ちいさな こえが した。",
                    "「こんにちは！ わたしは シェフうさぎ。",
                    "ざいりょうを さがす おてつだいを しましょうか？」"
                ],
                characterDialogue: "「もりには いろんな ざいりょうが あるよ。いっしょに さがしに いこう！」",
                interaction: .tapCharacter,
                nextNodeId: "challenge_1",
                choices: []
            ),

            // ── シーン2：問題発生（挑戦） ──
            "challenge_1": StoryNode(
                id: "challenge_1",
                scene: .challenge,
                background: .forest,
                narration: [
                    "ふたりは もりへ でかけた。",
                    "もりの なかは しずかで きれいだった。",
                    "でも とつぜん あめが ふってきた！"
                ],
                characterDialogue: "「きゃあ！ ざいりょうが ぬれちゃう！ どう しよう！」",
                interaction: .tapToContinue,
                nextNodeId: "challenge_2",
                choices: []
            ),

            "challenge_2": StoryNode(
                id: "challenge_2",
                scene: .challenge,
                background: .forest,
                narration: [
                    "あまがり に なるまで きの した で やすむことに。",
                    "でも もりの どうぶつたちが こまっていた。",
                    "こりすが たいせつな どんぐりを なくして ないていた。"
                ],
                characterDialogue: "「どうしよう… じかんが かかっちゃう。ケーキ つくれるかな…」",
                interaction: .choice,
                nextNodeId: nil,
                choices: [
                    StoryChoice(
                        id: "choice_ignore",
                        text: "いそぐから そのまま いく",
                        emoji: "🏃",
                        nextNodeId: "choice_kindness",
                        feedback: "シェフうさぎが やさしく おしえてくれた。"
                    ),
                    StoryChoice(
                        id: "choice_help",
                        text: "こりすの どんぐりを てつだう",
                        emoji: "🤝",
                        nextNodeId: "cooperation_1",
                        feedback: "きみは やさしいね！ きっと いいことが あるよ！"
                    )
                ]
            ),

            "choice_kindness": StoryNode(
                id: "choice_kindness",
                scene: .challenge,
                background: .forest,
                narration: [
                    "シェフうさぎが そっと いった。"
                ],
                characterDialogue: "「まってて。だれかが こまっているとき、すこしの やさしさが、おおきな ちがいを うむの。 てつだって あげましょ？」",
                interaction: .tapCharacter,
                nextNodeId: "cooperation_1",
                choices: []
            ),

            // ── シーン3：協力して解決 ──
            "cooperation_1": StoryNode(
                id: "cooperation_1",
                scene: .cooperation,
                background: .forest,
                narration: [
                    "きみと シェフうさぎは こりすの どんぐりを さがした。",
                    "きの ねもとに かくれていた どんぐりを みつけた！",
                    "こりすは とびあがって よろこんだ。"
                ],
                characterDialogue: "「ありがとう！ おれいに…これ、もりの たまごだよ！ おいしい ケーキが できるよ！」",
                interaction: .tapCharacter,
                nextNodeId: "cooperation_2",
                choices: []
            ),

            "cooperation_2": StoryNode(
                id: "cooperation_2",
                scene: .cooperation,
                background: .kitchen,
                narration: [
                    "もりの おくりもの が いっぱい！",
                    "ざいりょうを もって うちに かえった。",
                    "さあ、ケーキを つくろう！"
                ],
                characterDialogue: "「ぼくが まぜかたを おしえるね。いっしょに つくろう！」",
                interaction: .tapToContinue,
                nextNodeId: "achievement_1",
                choices: []
            ),

            // ── シーン4：夢の実現 ──
            "achievement_1": StoryNode(
                id: "achievement_1",
                scene: .achievement,
                background: .kitchen,
                narration: [
                    "まぜて、まぜて、まぜて…",
                    "オーブンから あまい においが ひろがる。",
                    "ふわふわの ケーキが できあがった！"
                ],
                characterDialogue: "「すごい！ とっても おいしそう！ やったね！」",
                interaction: .tapToContinue,
                nextNodeId: "achievement_2",
                choices: []
            ),

            "achievement_2": StoryNode(
                id: "achievement_2",
                scene: .achievement,
                background: .celebration,
                narration: [
                    "もりの どうぶつたちも みんな きてくれた。",
                    "ケーキを たべると、みんな えがおに なった。",
                    "きみの ケーキが、みんなを しあわせに した！"
                ],
                characterDialogue: "「おいしい！ えがおが うつる まほうの ケーキだね！」",
                interaction: .celebration,
                nextNodeId: "ending",
                choices: []
            ),

            "ending": StoryNode(
                id: "ending",
                scene: .ending,
                background: .celebration,
                narration: [
                    "やさしい きもちで つくった ケーキは、",
                    "みんなを えがおに する まほうが あった。",
                    "「ひとを しあわせにする ちからが、ゆめの はじまり。」"
                ],
                characterDialogue: "「また いっしょに つくろうね！ ありがとう！」",
                interaction: .celebration,
                nextNodeId: nil,
                choices: []
            )
        ]

        return Story(
            dreamType: .baker,
            nodes: nodes,
            startNodeId: "intro_1"
        )
    }
}
