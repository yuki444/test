import SwiftUI

struct LevelDashboardView: View {
    @EnvironmentObject var store: TreasureStore
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(
                    colors: [Color(hex: "#FFF9C4"), Color(hex: "#E8F5E9")],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 14) {
                        totalCard
                        ForEach(store.categories) { category in
                            CategoryLevelCard(
                                category: category,
                                count: store.count(for: category.id)
                            )
                        }
                        levelLegend
                    }
                    .padding(.vertical)
                }
            }
            .navigationTitle("⭐ レベル")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 26))
                            .foregroundColor(Color(hex: "#8D6E63"))
                    }
                }
            }
        }
    }

    private var totalCard: some View {
        HStack {
            statPill(value: "\(store.items.count)", label: "ぜんぶ", color: Color(hex: "#FF6B6B"))
            Divider().frame(height: 50)
            statPill(value: "\(store.categories.filter { store.count(for: $0.id) > 0 }.count)", label: "カテゴリー", color: Color(hex: "#4CAF50"))
            Divider().frame(height: 50)
            let total = store.categories.map { LevelSystem.levelIndex(for: store.count(for: $0.id)) }.reduce(0, +)
            statPill(value: "\(total)", label: "ごうけいLv", color: Color(hex: "#FF9800"))
        }
        .padding()
        .background(Color.white.opacity(0.9))
        .cornerRadius(18)
        .shadow(color: .gray.opacity(0.1), radius: 6)
        .padding(.horizontal)
    }

    private func statPill(value: String, label: String, color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 40, weight: .black, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(.system(size: 13, design: .rounded))
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
    }

    private var levelLegend: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("レベルひょう")
                .font(.system(size: 18, weight: .bold, design: .rounded))
                .foregroundColor(Color(hex: "#5D4037"))
                .padding(.horizontal)

            ForEach(Array(LevelSystem.thresholds.enumerated()), id: \.0) { idx, threshold in
                HStack(spacing: 12) {
                    Text(threshold.2)
                        .font(.system(size: 28))
                        .frame(width: 44)
                    Text("Lv\(idx)  \(threshold.1)")
                        .font(.system(size: 17, weight: .semibold, design: .rounded))
                        .foregroundColor(Color(hex: "#5D4037"))
                    Spacer()
                    Text(idx == 0 ? "0こから" : "\(threshold.0)こから")
                        .font(.system(size: 14, design: .rounded))
                        .foregroundColor(.gray)
                }
                .padding(.horizontal)
            }
        }
        .padding(.vertical, 14)
        .background(Color.white.opacity(0.85))
        .cornerRadius(18)
        .shadow(color: .gray.opacity(0.08), radius: 6)
        .padding(.horizontal)
    }
}

struct CategoryLevelCard: View {
    let category: TreasureCategory
    let count: Int

    var body: some View {
        let info = LevelSystem.info(for: count)

        HStack(spacing: 14) {
            ZStack(alignment: .bottomTrailing) {
                Text(category.emoji)
                    .font(.system(size: 46))
                    .frame(width: 64, height: 64)
                    .background(category.color.opacity(0.14))
                    .cornerRadius(14)

                Text("Lv\(info.level)")
                    .font(.system(size: 11, weight: .black, design: .rounded))
                    .foregroundColor(.white)
                    .padding(.horizontal, 5)
                    .padding(.vertical, 2)
                    .background(category.color)
                    .cornerRadius(8)
                    .offset(x: 6, y: 6)
            }

            VStack(alignment: .leading, spacing: 5) {
                HStack {
                    Text(category.name)
                        .font(.system(size: 19, weight: .bold, design: .rounded))
                        .foregroundColor(Color(hex: "#5D4037"))
                    Spacer()
                    Text(info.emoji + " " + info.title)
                        .font(.system(size: 15, weight: .semibold, design: .rounded))
                        .foregroundColor(category.color)
                }

                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 5)
                            .fill(Color.gray.opacity(0.18))
                            .frame(height: 10)
                        RoundedRectangle(cornerRadius: 5)
                            .fill(category.color)
                            .frame(width: geo.size.width * CGFloat(info.progress), height: 10)
                            .animation(.spring(), value: info.progress)
                    }
                }
                .frame(height: 10)

                HStack {
                    Text("\(count)こ　とった！")
                        .font(.system(size: 13, design: .rounded))
                        .foregroundColor(.gray)
                    Spacer()
                    if let next = info.nextCount {
                        Text("あと\(next - count)こ")
                            .font(.system(size: 13, weight: .bold, design: .rounded))
                            .foregroundColor(category.color)
                    } else {
                        Text("かんぺき！🏆")
                            .font(.system(size: 13, weight: .bold, design: .rounded))
                            .foregroundColor(.orange)
                    }
                }
            }
        }
        .padding()
        .background(Color.white.opacity(0.9))
        .cornerRadius(18)
        .shadow(color: .gray.opacity(0.08), radius: 6)
        .padding(.horizontal)
    }
}
