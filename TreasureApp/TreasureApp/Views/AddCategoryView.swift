import SwiftUI

struct AddCategoryView: View {
    @EnvironmentObject var store: TreasureStore
    @Environment(\.dismiss) var dismiss

    @State private var name = ""
    @State private var selectedEmoji = "🌟"

    private let emojiOptions = [
        "🌟","🎵","🍎","🏖","🦕","🚀","🎨","🎮",
        "🍕","🌺","🐶","🐱","🦋","🏀","🎸","🍦"
    ]

    private let colorOptions: [(String, String)] = [
        ("#9C27B0", "むらさき"), ("#E91E63", "ぴんく"), ("#F44336", "あか"),
        ("#FF9800", "おれんじ"), ("#607D8B", "グレー"), ("#00BCD4", "みずいろ"),
    ]
    @State private var selectedColor = "#9C27B0"

    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "#FFFDE7").ignoresSafeArea()

                VStack(spacing: 24) {
                    // Preview
                    VStack(spacing: 8) {
                        Text(selectedEmoji)
                            .font(.system(size: 64))
                            .frame(width: 100, height: 100)
                            .background(Color(hex: selectedColor))
                            .cornerRadius(22)
                            .shadow(color: Color(hex: selectedColor).opacity(0.4), radius: 10)

                        if !name.isEmpty {
                            Text(name)
                                .font(.system(size: 20, weight: .bold, design: .rounded))
                                .foregroundColor(Color(hex: selectedColor))
                        }
                    }
                    .padding(.top)

                    // Name input (hiragana hint)
                    VStack(alignment: .leading, spacing: 6) {
                        Text("なまえ")
                            .font(.system(size: 17, weight: .bold, design: .rounded))
                            .foregroundColor(Color(hex: "#5D4037"))
                            .padding(.horizontal)

                        TextField("　れい：たべもの", text: $name)
                            .font(.system(size: 22, design: .rounded))
                            .padding()
                            .background(Color.white)
                            .cornerRadius(14)
                            .shadow(color: .gray.opacity(0.1), radius: 4)
                            .padding(.horizontal)
                    }

                    // Emoji picker
                    VStack(alignment: .leading, spacing: 6) {
                        Text("えもじ")
                            .font(.system(size: 17, weight: .bold, design: .rounded))
                            .foregroundColor(Color(hex: "#5D4037"))
                            .padding(.horizontal)

                        LazyVGrid(
                            columns: Array(repeating: GridItem(.flexible()), count: 8),
                            spacing: 8
                        ) {
                            ForEach(emojiOptions, id: \.self) { emoji in
                                Button {
                                    selectedEmoji = emoji
                                } label: {
                                    Text(emoji)
                                        .font(.system(size: 30))
                                        .frame(width: 44, height: 44)
                                        .background(selectedEmoji == emoji ? Color(hex: selectedColor).opacity(0.25) : Color.white)
                                        .cornerRadius(10)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 10)
                                                .stroke(selectedEmoji == emoji ? Color(hex: selectedColor) : Color.clear, lineWidth: 2)
                                        )
                                }
                            }
                        }
                        .padding(.horizontal)
                    }

                    // Color picker
                    VStack(alignment: .leading, spacing: 6) {
                        Text("いろ")
                            .font(.system(size: 17, weight: .bold, design: .rounded))
                            .foregroundColor(Color(hex: "#5D4037"))
                            .padding(.horizontal)

                        HStack(spacing: 12) {
                            ForEach(colorOptions, id: \.0) { (hex, _) in
                                Button {
                                    selectedColor = hex
                                } label: {
                                    Circle()
                                        .fill(Color(hex: hex))
                                        .frame(width: 44, height: 44)
                                        .overlay(
                                            Circle()
                                                .stroke(Color.white, lineWidth: selectedColor == hex ? 3 : 0)
                                                .padding(3)
                                        )
                                        .shadow(color: Color(hex: hex).opacity(0.5), radius: 4)
                                }
                            }
                        }
                        .padding(.horizontal)
                    }

                    Spacer()

                    // Add button
                    Button {
                        guard !name.trimmingCharacters(in: .whitespaces).isEmpty else { return }
                        store.addCustomCategory(
                            name: name.trimmingCharacters(in: .whitespaces),
                            emoji: selectedEmoji,
                            colorHex: selectedColor
                        )
                        dismiss()
                    } label: {
                        Text("ついかする！")
                            .font(.system(size: 22, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(
                                name.trimmingCharacters(in: .whitespaces).isEmpty
                                    ? Color.gray.opacity(0.4)
                                    : Color(hex: selectedColor)
                            )
                            .cornerRadius(18)
                            .shadow(color: Color(hex: selectedColor).opacity(0.4), radius: 8, x: 0, y: 4)
                    }
                    .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                    .padding(.horizontal)
                    .padding(.bottom)
                }
            }
            .navigationTitle("カテゴリーをついか")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark")
                            .foregroundColor(Color(hex: "#8D6E63"))
                    }
                }
            }
        }
    }
}
