import SwiftUI

struct HomeView: View {
    @EnvironmentObject var store: TreasureStore
    @State private var selectedCategory: TreasureCategory?
    @State private var showCamera = false
    @State private var showGallery = false
    @State private var showLevels = false
    @State private var showAddCategory = false

    let columns = [GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(
                    colors: [Color(hex: "#FFF9C4"), Color(hex: "#E1F5FE")],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()

                VStack(spacing: 16) {
                    headerView
                    categoryGrid
                    bottomButtons
                }
            }
        }
        .fullScreenCover(isPresented: $showCamera) {
            if let category = selectedCategory {
                CameraView(category: category)
                    .environmentObject(store)
            }
        }
        .sheet(isPresented: $showGallery) {
            GalleryView().environmentObject(store)
        }
        .sheet(isPresented: $showLevels) {
            LevelDashboardView().environmentObject(store)
        }
        .sheet(isPresented: $showAddCategory) {
            AddCategoryView().environmentObject(store)
        }
    }

    private var headerView: some View {
        HStack {
            Text("🎁")
                .font(.system(size: 44))
            VStack(alignment: .leading, spacing: 2) {
                Text("たからもの")
                    .font(.system(size: 28, weight: .black, design: .rounded))
                    .foregroundColor(Color(hex: "#5D4037"))
                Text("はっけん！")
                    .font(.system(size: 20, weight: .bold, design: .rounded))
                    .foregroundColor(Color(hex: "#8D6E63"))
            }
            Spacer()
            Button {
                showLevels = true
            } label: {
                Image(systemName: "star.fill")
                    .font(.system(size: 26))
                    .foregroundColor(.yellow)
                    .padding(12)
                    .background(Color.white.opacity(0.9))
                    .clipShape(Circle())
                    .shadow(color: .yellow.opacity(0.4), radius: 6)
            }
        }
        .padding(.horizontal)
        .padding(.top)
    }

    private var categoryGrid: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 14) {
                ForEach(store.categories) { category in
                    CategoryButton(
                        category: category,
                        count: store.count(for: category.id)
                    ) {
                        selectedCategory = category
                        showCamera = true
                    }
                }
                // Add custom category button
                AddCategoryButton {
                    showAddCategory = true
                }
            }
            .padding(.horizontal)
        }
    }

    private var bottomButtons: some View {
        Button {
            showGallery = true
        } label: {
            HStack(spacing: 10) {
                Image(systemName: "photo.on.rectangle.angled")
                    .font(.system(size: 26))
                Text("ギャラリー")
                    .font(.system(size: 22, weight: .bold, design: .rounded))
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                LinearGradient(
                    colors: [Color(hex: "#FF6B6B"), Color(hex: "#FF8E53")],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .cornerRadius(20)
            .shadow(color: .orange.opacity(0.4), radius: 8, x: 0, y: 4)
        }
        .padding(.horizontal)
        .padding(.bottom)
    }
}

struct CategoryButton: View {
    let category: TreasureCategory
    let count: Int
    let action: () -> Void

    @State private var isPressed = false

    var levelInfo: LevelInfo { LevelSystem.info(for: count) }

    var body: some View {
        Button {
            withAnimation(.spring(response: 0.25, dampingFraction: 0.6)) {
                isPressed = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                withAnimation { isPressed = false }
                action()
            }
        } label: {
            ZStack(alignment: .topTrailing) {
                VStack(spacing: 6) {
                    Text(category.emoji)
                        .font(.system(size: 52))
                    Text(category.name)
                        .font(.system(size: 16, weight: .bold, design: .rounded))
                        .foregroundColor(.white)
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                    // Count badge
                    Text("\(count)こ")
                        .font(.system(size: 13, weight: .semibold, design: .rounded))
                        .foregroundColor(.white.opacity(0.85))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
                .background(category.color)
                .cornerRadius(20)
                .shadow(color: category.color.opacity(0.45), radius: 8, x: 0, y: 4)
                .scaleEffect(isPressed ? 0.93 : 1.0)

                // Level badge
                Text("Lv\(levelInfo.level)")
                    .font(.system(size: 12, weight: .black, design: .rounded))
                    .foregroundColor(.white)
                    .padding(.horizontal, 7)
                    .padding(.vertical, 3)
                    .background(Color.black.opacity(0.35))
                    .cornerRadius(10)
                    .offset(x: -8, y: 8)
            }
        }
    }
}

struct AddCategoryButton: View {
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: "plus")
                    .font(.system(size: 36, weight: .bold))
                    .foregroundColor(Color(hex: "#9E9E9E"))
                Text("ついか")
                    .font(.system(size: 16, weight: .bold, design: .rounded))
                    .foregroundColor(Color(hex: "#9E9E9E"))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 26)
            .background(Color.white.opacity(0.6))
            .cornerRadius(20)
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(style: StrokeStyle(lineWidth: 2, dash: [8]))
                    .foregroundColor(Color(hex: "#BDBDBD"))
            )
        }
    }
}
