import SwiftUI

struct CategoryGalleryView: View {
    @EnvironmentObject var store: TreasureStore
    @Environment(\.dismiss) var dismiss
    let category: TreasureCategory

    let columns = [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())]
    @State private var selectedItem: TreasureItem?

    var categoryItems: [TreasureItem] { store.items(for: category.id) }

    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "#FFF8E1").ignoresSafeArea()

                VStack(spacing: 0) {
                    levelCard
                        .padding()

                    ScrollView {
                        LazyVGrid(columns: columns, spacing: 3) {
                            ForEach(categoryItems) { item in
                                Button { selectedItem = item } label: {
                                    ThumbnailView(item: item)
                                        .aspectRatio(1, contentMode: .fill)
                                }
                                .environmentObject(store)
                            }
                        }
                        .padding(.horizontal)
                        .padding(.bottom)
                    }
                }
            }
            .navigationTitle(category.emoji + " " + category.name)
            .navigationBarTitleDisplayMode(.inline)
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
        .sheet(item: $selectedItem) { item in
            TreasureDetailView(item: item, category: category)
                .environmentObject(store)
        }
    }

    private var levelCard: some View {
        let info = LevelSystem.info(for: categoryItems.count)

        return HStack(spacing: 14) {
            ZStack(alignment: .bottomTrailing) {
                Text(info.emoji)
                    .font(.system(size: 44))
                    .frame(width: 60, height: 60)
                    .background(category.color.opacity(0.15))
                    .cornerRadius(14)

                Text("Lv\(info.level)")
                    .font(.system(size: 11, weight: .black, design: .rounded))
                    .foregroundColor(.white)
                    .padding(.horizontal, 5)
                    .padding(.vertical, 2)
                    .background(category.color)
                    .cornerRadius(7)
                    .offset(x: 6, y: 6)
            }

            VStack(alignment: .leading, spacing: 5) {
                HStack {
                    Text(info.title)
                        .font(.system(size: 20, weight: .bold, design: .rounded))
                        .foregroundColor(category.color)
                    Spacer()
                    Text("\(categoryItems.count)こ")
                        .font(.system(size: 22, weight: .black, design: .rounded))
                        .foregroundColor(category.color)
                }

                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 6)
                            .fill(Color.gray.opacity(0.2))
                            .frame(height: 12)
                        RoundedRectangle(cornerRadius: 6)
                            .fill(category.color)
                            .frame(width: geo.size.width * CGFloat(info.progress), height: 12)
                            .animation(.spring(), value: info.progress)
                    }
                }
                .frame(height: 12)

                if let next = info.nextCount {
                    Text("あと\(next - categoryItems.count)こで　つぎのレベル！")
                        .font(.system(size: 13, design: .rounded))
                        .foregroundColor(.gray)
                } else {
                    Text("さいこうレベル　たっせい！🏆")
                        .font(.system(size: 13, weight: .bold, design: .rounded))
                        .foregroundColor(.orange)
                }
            }
        }
        .padding()
        .background(Color.white.opacity(0.9))
        .cornerRadius(18)
        .shadow(color: .gray.opacity(0.1), radius: 6)
    }
}
