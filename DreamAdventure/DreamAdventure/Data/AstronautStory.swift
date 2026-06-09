import Foundation

// 宇宙飛行士ストーリー：「ほしへの たび」
// 動物：コスモくま 🐻
// テーマ：あきらめない心・友達と協力する大切さ

extension StoryData {
    static var astronautStory: Story {
        let nodes: [String: StoryNode] = [

            // ── シーン1：夜空を見上げて（共感） ──
            "intro_1": StoryNode(
                id: "intro_1",
                scene: .opening,
                background: .nightSky,
                narration: [
                    "まいにち よる、きみは そらを みあげた。",
                    "きらきら かがやく ほし。",
                    "「いつか あの ほしに いきたいな…」"
                ],
                characterDialogue: nil,
                interaction: .tapToContinue,
                nextNodeId: "intro_2",
                choices: []
            ),

            "intro_2": StoryNode(
                id: "intro_2",
                scene: .opening,
                background: .nightSky,
                narration: [
                    "ある あさ、ふしぎな ことが おきた。",
                    "まどの そとに、ちいさな くまさんが たっている！",
                    "くまさんの せなかには、ちいさな ロケットが ついていた。"
                ],
                characterDialogue: "「やあ！ ぼくは コスモくま。きみを うちゅうに つれていきに きたよ！」",
                interaction: .tapCharacter,
                nextNodeId: "intro_3",
                choices: []
            ),

            "intro_3": StoryNode(
                id: "intro_3",
                scene: .opening,
                background: .spaceship,
                narration: [
                    "コスモくまの ロケットに のって、",
                    "ふたりは おそらへ とびたった！",
                    "まちが どんどん ちいさく なっていく。"
                ],
                characterDialogue: "「うわあ！ きれい！ ほしが ちかい！」",
                interaction: .tapToContinue,
                nextNodeId: "challenge_1",
                choices: []
            ),

            // ── シーン2：問題発生（挑戦） ──
            "challenge_1": StoryNode(
                id: "challenge_1",
                scene: .challenge,
                background: .spaceship,
                narration: [
                    "ところが とつぜん…",
                    "ガタン！ ガタン！",
                    "ロケットが ふるえだした！"
                ],
                characterDialogue: "「たいへんだ！ エンジンが こわれちゃった！ このままじゃ ほしに いけない…」",
                interaction: .tapToContinue,
                nextNodeId: "challenge_2",
                choices: []
            ),

            "challenge_2": StoryNode(
                id: "challenge_2",
                scene: .challenge,
                background: .moon,
                narration: [
                    "ロケットは つきの うえに ちゃくりくした。",
                    "しずかな つきの せかい。",
                    "こわれた エンジンを なおさないと いけない。"
                ],
                characterDialogue: "「コスモくま、どうしよう…」",
                interaction: .choice,
                nextNodeId: nil,
                choices: [
                    StoryChoice(
                        id: "choice_give_up",
                        text: "あきらめて かえる",
                        emoji: "😢",
                        nextNodeId: "choice_encouragement",
                        feedback: "コスモくまが やさしく はなしかけた。"
                    ),
                    StoryChoice(
                        id: "choice_try",
                        text: "いっしょに なおそうとする",
                        emoji: "💪",
                        nextNodeId: "cooperation_1",
                        feedback: "やってみよう！ きっと できるよ！"
                    )
                ]
            ),

            // あきらめ選択への励まし
            "choice_encouragement": StoryNode(
                id: "choice_encouragement",
                scene: .challenge,
                background: .moon,
                narration: [
                    "コスモくまは きみの てを そっと にぎった。"
                ],
                characterDialogue: "「だいじょうぶだよ。ふたりなら きっと できる。いっしょに やってみよう？」",
                interaction: .tapCharacter,
                nextNodeId: "cooperation_1",
                choices: []
            ),

            // ── シーン3：協力して解決 ──
            "cooperation_1": StoryNode(
                id: "cooperation_1",
                scene: .cooperation,
                background: .moon,
                narration: [
                    "きみは コスモくまと いっしょに エンジンを しらべた。",
                    "「ここの ねじが ゆるんでる！」",
                    "コスモくまが どうぐを わたしてくれた。"
                ],
                characterDialogue: "「そう！ その ねじを まわして！ ぼくが ここを おさえてるから！」",
                interaction: .tapCharacter,
                nextNodeId: "cooperation_2",
                choices: []
            ),

            "cooperation_2": StoryNode(
                id: "cooperation_2",
                scene: .cooperation,
                background: .stars,
                narration: [
                    "きみが ねじを まわすと…",
                    "ピカッ！",
                    "エンジンが ひかりはじめた！"
                ],
                characterDialogue: "「やった！ なおった！ きみって すごいね！ うちゅうひこうし みたいだよ！」",
                interaction: .tapToContinue,
                nextNodeId: "achievement_1",
                choices: []
            ),

            // ── シーン4：夢の実現 ──
            "achievement_1": StoryNode(
                id: "achievement_1",
                scene: .achievement,
                background: .cosmos,
                narration: [
                    "ロケットは もう いちど とびたった！",
                    "どんどん どんどん のぼっていく。",
                    "まるい ちきゅうが みえてきた。"
                ],
                characterDialogue: "「みて！ ちきゅうだよ！ まるくて きれいだね！」",
                interaction: .tapToContinue,
                nextNodeId: "achievement_2",
                choices: []
            ),

            "achievement_2": StoryNode(
                id: "achievement_2",
                scene: .achievement,
                background: .stars,
                narration: [
                    "きみは うちゅうの まんなかで、",
                    "かぞえきれない ほしたちに かこまれた。",
                    "ゆめに みた けしきが、すぐ そこに あった。"
                ],
                characterDialogue: "「ありがとう。いっしょに きてくれて。ともだちって いいね。」",
                interaction: .celebration,
                nextNodeId: "ending",
                choices: []
            ),

            "ending": StoryNode(
                id: "ending",
                scene: .ending,
                background: .stars,
                narration: [
                    "その よる、きみは もういちど そらを みあげた。",
                    "ほしが まえより すこし ちかく みえた。",
                    "「あきらめなければ、ゆめは かなう。」"
                ],
                characterDialogue: "「また いっしょに ぼうけん しようね！」",
                interaction: .celebration,
                nextNodeId: nil,
                choices: []
            )
        ]

        return Story(
            dreamType: .astronaut,
            nodes: nodes,
            startNodeId: "intro_1"
        )
    }
}
