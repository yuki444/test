import SwiftUI

struct GalleryView: View {
    @EnvironmentObject var store: TreasureStore
    @Environment(\.dismiss) var dismiss
    @State private var selectedCategory: TreasureCategory?

    let columns = [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "#FFF8E1").ignoresSafeArea()

                if store.items.isEmpty {
                    emptyState
                } else {
                    ScrollView {
                        VStack(spacing: 16) {
                            ForEach(store.categories) { category in
                                let categoryItems = store.items(for: category.id)
                                if !categoryItems.isEmpty {
                                    CategorySection(
                                        category: category,
                                        items: categoryItems,
                                        columns: columns
                                    ) {
                                        selectedCategory = category
                                    }
                                }
                            }
                        }
                        .padding(.vertical)
                    }
                }
            }
            .navigationTitle("ギャラリー")
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
        .sheet(item: $selectedCategory) { category in
            CategoryGalleryView(category: category).environmentObject(store)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 20) {
            Text("📷")
                .font(.system(size: 80))
            Text("まだたからものが\nないよ")
                .font(.system(size: 26, weight: .bold, design: .rounded))
                .foregroundColor(Color(hex: "#8D6E63"))
                .multilineTextAlignment(.center)
            Text("しゃしんをとって\nたからものをあつめよう！")
                .font(.system(size: 18, design: .rounded))
                .foregroundColor(Color(hex: "#A1887F"))
                .multilineTextAlignment(.center)
        }
    }
}

struct CategorySection: View {
    @EnvironmentObject var store: TreasureStore
    let category: TreasureCategory
    let items: [TreasureItem]
    let columns: [GridItem]
    let onSeeMore: () -> Void

    private let maxShown = 6

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(category.emoji)
                    .font(.system(size: 28))
                Text(category.name)
                    .font(.system(size: 20, weight: .bold, design: .rounded))
                    .foregroundColor(category.color)
                Spacer()
                Text("\(items.count)こ")
                    .font(.system(size: 17, weight: .semibold, design: .rounded))
                    .foregroundColor(category.color)
            }
            .padding(.horizontal)

            LazyVGrid(columns: columns, spacing: 3) {
                ForEach(items.prefix(maxShown)) { item in
                    ThumbnailView(item: item)
                        .aspectRatio(1, contentMode: .fill)
                }
                if items.count > maxShown {
                    Button(action: onSeeMore) {
                        ZStack {
                            category.color.opacity(0.15)
                            VStack(spacing: 4) {
                                Text("+\(items.count - maxShown)")
                                    .font(.system(size: 22, weight: .bold, design: .rounded))
                                    .foregroundColor(category.color)
                                Text("もっとみる")
                                    .font(.system(size: 12, weight: .semibold, design: .rounded))
                                    .foregroundColor(category.color)
                            }
                        }
                        .aspectRatio(1, contentMode: .fill)
                    }
                }
            }
            .cornerRadius(10)
            .padding(.horizontal)
        }
        .padding(.vertical, 10)
        .background(Color.white.opacity(0.85))
        .cornerRadius(18)
        .shadow(color: .gray.opacity(0.08), radius: 6)
        .padding(.horizontal)
    }
}

struct ThumbnailView: View {
    @EnvironmentObject var store: TreasureStore
    let item: TreasureItem

    var body: some View {
        Group {
            if let img = store.loadImage(filename: item.imageFilename) {
                Image(uiImage: img)
                    .resizable()
                    .scaledToFill()
            } else {
                Color.gray.opacity(0.25)
                    .overlay(
                        Image(systemName: "photo")
                            .foregroundColor(.gray)
                    )
            }
        }
        .clipped()
    }
}
