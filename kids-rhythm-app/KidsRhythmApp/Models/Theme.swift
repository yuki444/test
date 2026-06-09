import SwiftUI

enum WaveformType: String, Codable {
    case sine, triangle, square, bounce
}

struct SoundButton: Identifiable, Codable {
    let id: Int
    let emoji: String
    let colorHex: String
    let frequency: Double
    let waveform: WaveformType

    var color: Color {
        Color(hex: colorHex)
    }
}

struct Theme: Identifiable {
    let id: Int
    let nameJP: String
    let emoji: String
    let gradientTop: Color
    let gradientBottom: Color
    let accentColor: Color
    let characterEmoji: String
    let buttons: [SoundButton]
    let particleEmoji: String
    let bpm: Double

    static let all: [Theme] = [
        Theme(
            id: 0,
            nameJP: "もり",
            emoji: "🌲",
            gradientTop: Color(hex: "#1a5c1a"),
            gradientBottom: Color(hex: "#5cb85c"),
            accentColor: Color(hex: "#90EE90"),
            characterEmoji: "🐿️",
            buttons: [
                SoundButton(id: 0, emoji: "🐦", colorHex: "#FFD700", frequency: 523.25, waveform: .bounce),
                SoundButton(id: 1, emoji: "🌿", colorHex: "#32CD32", frequency: 392.00, waveform: .bounce),
                SoundButton(id: 2, emoji: "🐸", colorHex: "#00CED1", frequency: 329.63, waveform: .bounce),
                SoundButton(id: 3, emoji: "🦉", colorHex: "#8B4513", frequency: 261.63, waveform: .bounce),
            ],
            particleEmoji: "🍀",
            bpm: 110
        ),
        Theme(
            id: 1,
            nameJP: "うちゅう",
            emoji: "🚀",
            gradientTop: Color(hex: "#0a0a2e"),
            gradientBottom: Color(hex: "#1a1a6e"),
            accentColor: Color(hex: "#7B68EE"),
            characterEmoji: "👽",
            buttons: [
                SoundButton(id: 0, emoji: "⭐", colorHex: "#FFD700", frequency: 440.00, waveform: .sine),
                SoundButton(id: 1, emoji: "🚀", colorHex: "#FF6347", frequency: 293.66, waveform: .sine),
                SoundButton(id: 2, emoji: "🌙", colorHex: "#C0C0C0", frequency: 220.00, waveform: .sine),
                SoundButton(id: 3, emoji: "🪐", colorHex: "#9370DB", frequency: 174.61, waveform: .sine),
            ],
            particleEmoji: "✨",
            bpm: 90
        ),
        Theme(
            id: 2,
            nameJP: "うみ",
            emoji: "🌊",
            gradientTop: Color(hex: "#003d99"),
            gradientBottom: Color(hex: "#00bfff"),
            accentColor: Color(hex: "#40E0D0"),
            characterEmoji: "🐬",
            buttons: [
                SoundButton(id: 0, emoji: "🌊", colorHex: "#1E90FF", frequency: 369.99, waveform: .triangle),
                SoundButton(id: 1, emoji: "🐚", colorHex: "#FF8C69", frequency: 493.88, waveform: .triangle),
                SoundButton(id: 2, emoji: "🫧", colorHex: "#87CEEB", frequency: 587.33, waveform: .triangle),
                SoundButton(id: 3, emoji: "🐠", colorHex: "#FF6347", frequency: 277.18, waveform: .triangle),
            ],
            particleEmoji: "🫧",
            bpm: 95
        ),
        Theme(
            id: 3,
            nameJP: "じゃんぐる",
            emoji: "🌴",
            gradientTop: Color(hex: "#2d5a1b"),
            gradientBottom: Color(hex: "#8bc34a"),
            accentColor: Color(hex: "#ADFF2F"),
            characterEmoji: "🐒",
            buttons: [
                SoundButton(id: 0, emoji: "🥁", colorHex: "#A0522D", frequency: 130.81, waveform: .square),
                SoundButton(id: 1, emoji: "🐒", colorHex: "#DAA520", frequency: 196.00, waveform: .square),
                SoundButton(id: 2, emoji: "🦜", colorHex: "#FF4500", frequency: 261.63, waveform: .square),
                SoundButton(id: 3, emoji: "🌧️", colorHex: "#4682B4", frequency: 392.00, waveform: .square),
            ],
            particleEmoji: "🍌",
            bpm: 130
        ),
        Theme(
            id: 4,
            nameJP: "のうじょう",
            emoji: "🐄",
            gradientTop: Color(hex: "#8B6914"),
            gradientBottom: Color(hex: "#F5DEB3"),
            accentColor: Color(hex: "#FFD700"),
            characterEmoji: "🐔",
            buttons: [
                SoundButton(id: 0, emoji: "🐄", colorHex: "#FFFFFF", frequency: 329.63, waveform: .bounce),
                SoundButton(id: 1, emoji: "🐷", colorHex: "#FFB6C1", frequency: 415.30, waveform: .bounce),
                SoundButton(id: 2, emoji: "🐑", colorHex: "#E8E8E8", frequency: 493.88, waveform: .bounce),
                SoundButton(id: 3, emoji: "🐔", colorHex: "#FF8C00", frequency: 659.25, waveform: .bounce),
            ],
            particleEmoji: "🌻",
            bpm: 105
        ),
        Theme(
            id: 5,
            nameJP: "まち",
            emoji: "🏙️",
            gradientTop: Color(hex: "#1c1c2e"),
            gradientBottom: Color(hex: "#4a4a8a"),
            accentColor: Color(hex: "#FF69B4"),
            characterEmoji: "🤖",
            buttons: [
                SoundButton(id: 0, emoji: "🚂", colorHex: "#DC143C", frequency: 349.23, waveform: .square),
                SoundButton(id: 1, emoji: "🔔", colorHex: "#FFD700", frequency: 523.25, waveform: .bounce),
                SoundButton(id: 2, emoji: "🎺", colorHex: "#FFA500", frequency: 440.00, waveform: .triangle),
                SoundButton(id: 3, emoji: "👏", colorHex: "#FF69B4", frequency: 261.63, waveform: .square),
            ],
            particleEmoji: "💡",
            bpm: 120
        ),
        Theme(
            id: 6,
            nameJP: "さばく",
            emoji: "🌵",
            gradientTop: Color(hex: "#8B4513"),
            gradientBottom: Color(hex: "#DEB887"),
            accentColor: Color(hex: "#FF8C00"),
            characterEmoji: "🦎",
            buttons: [
                SoundButton(id: 0, emoji: "🌵", colorHex: "#228B22", frequency: 246.94, waveform: .triangle),
                SoundButton(id: 1, emoji: "💨", colorHex: "#87CEEB", frequency: 185.00, waveform: .sine),
                SoundButton(id: 2, emoji: "🦂", colorHex: "#FF6347", frequency: 369.99, waveform: .triangle),
                SoundButton(id: 3, emoji: "🐪", colorHex: "#D2691E", frequency: 146.83, waveform: .sine),
            ],
            particleEmoji: "⭐",
            bpm: 85
        ),
        Theme(
            id: 7,
            nameJP: "こおり",
            emoji: "❄️",
            gradientTop: Color(hex: "#add8e6"),
            gradientBottom: Color(hex: "#e0f4ff"),
            accentColor: Color(hex: "#00BFFF"),
            characterEmoji: "🐧",
            buttons: [
                SoundButton(id: 0, emoji: "❄️", colorHex: "#87CEEB", frequency: 493.88, waveform: .sine),
                SoundButton(id: 1, emoji: "🐧", colorHex: "#1C1C1C", frequency: 329.63, waveform: .sine),
                SoundButton(id: 2, emoji: "🌨️", colorHex: "#B0E0E6", frequency: 261.63, waveform: .triangle),
                SoundButton(id: 3, emoji: "🦭", colorHex: "#778899", frequency: 196.00, waveform: .sine),
            ],
            particleEmoji: "❄️",
            bpm: 88
        ),
        Theme(
            id: 8,
            nameJP: "にじ",
            emoji: "🌈",
            gradientTop: Color(hex: "#ff9a9e"),
            gradientBottom: Color(hex: "#fad0c4"),
            accentColor: Color(hex: "#FF1493"),
            characterEmoji: "🦄",
            buttons: [
                SoundButton(id: 0, emoji: "🎵", colorHex: "#FF6B9D", frequency: 523.25, waveform: .bounce),
                SoundButton(id: 1, emoji: "🎶", colorHex: "#C850C0", frequency: 659.25, waveform: .bounce),
                SoundButton(id: 2, emoji: "✨", colorHex: "#FFDD57", frequency: 392.00, waveform: .bounce),
                SoundButton(id: 3, emoji: "🌈", colorHex: "#48CFAD", frequency: 783.99, waveform: .bounce),
            ],
            particleEmoji: "🌟",
            bpm: 115
        ),
        Theme(
            id: 9,
            nameJP: "おかし",
            emoji: "🍭",
            gradientTop: Color(hex: "#ff6eb4"),
            gradientBottom: Color(hex: "#ffc3e1"),
            accentColor: Color(hex: "#FF69B4"),
            characterEmoji: "🧁",
            buttons: [
                SoundButton(id: 0, emoji: "🍭", colorHex: "#FF1493", frequency: 784.00, waveform: .bounce),
                SoundButton(id: 1, emoji: "🍬", colorHex: "#FF69B4", frequency: 587.33, waveform: .bounce),
                SoundButton(id: 2, emoji: "🎂", colorHex: "#FFD700", frequency: 493.88, waveform: .bounce),
                SoundButton(id: 3, emoji: "🍩", colorHex: "#FF8C00", frequency: 392.00, waveform: .bounce),
            ],
            particleEmoji: "🍬",
            bpm: 125
        ),
    ]
}

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(.sRGB, red: Double(r) / 255, green: Double(g) / 255, blue: Double(b) / 255, opacity: Double(a) / 255)
    }
}
