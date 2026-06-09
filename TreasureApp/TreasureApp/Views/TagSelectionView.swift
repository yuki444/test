import SwiftUI

struct TagSelectionView: View {
    @EnvironmentObject var store: TreasureStore
    @Environment(\.dismiss) var dismiss

    let image: UIImage
    let category: TreasureCategory

    @State private var selectedSubcategory = ""
    @State private var showCelebration = false
    @State private var isNewLevel = false

    private var canSave: Bool {
        category.subcategories.isEmpty || !selectedSubcategory.isEmpty
    }

    var body: some View {
        ZStack {
            Color(hex: "#FFFDE7").ignoresSafeArea()

            VStack(spacing: 18) {
                // Photo preview
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(height: 260)
                    .clipped()
                    .cornerRadius(20)
                    .shadow(radius: 8)
                    .padding(.horizontal)
                    .padding(.top)

                // Category label
                HStack(spacing: 8) {
                    Text(category.emoji)
                        .font(.system(size: 38))
                    Text(category.name)
                        .font(.system(size: 26, weight: .bold, design: .rounded))
                        .foregroundColor(category.color)
                }

                // Subcategory picker
                if !category.subcategories.isEmpty {
                    Text("なにを　みつけたの？")
                        .font(.system(size: 20, weight: .semibold, design: .rounded))
                        .foregroundColor(Color(hex: "#5D4037"))

                    LazyVGrid(
                        columns: [GridItem(.flexible()), GridItem(.flexible())],
                        spacing: 12
                    ) {
                        ForEach(category.subcategories, id: \.self) { sub in
                            SubcategoryButton(
                                name: sub,
                                isSelected: selectedSubcategory == sub,
                                color: category.color
                            ) {
                                selectedSubcategory = sub
                            }
                        }
                    }
                    .padding(.horizontal)
                }

                Spacer()

                // Save button
                Button { saveTreasure() } label: {
                    HStack(spacing: 8) {
                        Text("🎁")
                            .font(.system(size: 26))
                        Text("たからものに　する！")
                            .font(.system(size: 20, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 18)
                    .background(canSave ? category.color : Color.gray.opacity(0.4))
                    .cornerRadius(20)
                    .shadow(color: canSave ? category.color.opacity(0.4) : .clear, radius: 8, x: 0, y: 4)
                }
                .disabled(!canSave)
                .padding(.horizontal)
                .padding(.bottom)
            }
        }
        .fullScreenCover(isPresented: $showCelebration) {
            CelebrationView(category: category, isNewLevel: isNewLevel) {
                dismiss()
            }
        }
    }

    private func saveTreasure() {
        let prevCount = store.count(for: category.id)
        let sub = category.subcategories.isEmpty ? category.name : selectedSubcategory
        store.addTreasure(image: image, categoryId: category.id, subcategory: sub)

        let newCount = store.count(for: category.id)
        isNewLevel = LevelSystem.levelIndex(for: newCount) > LevelSystem.levelIndex(for: prevCount)
        showCelebration = true
    }
}

struct SubcategoryButton: View {
    let name: String
    let isSelected: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(name)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundColor(isSelected ? .white : color)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .background(isSelected ? color : color.opacity(0.12))
                .cornerRadius(14)
                .overlay(
                    RoundedRectangle(cornerRadius: 14)
                        .stroke(color, lineWidth: 2)
                )
                .scaleEffect(isSelected ? 1.04 : 1.0)
                .animation(.spring(response: 0.2), value: isSelected)
        }
    }
}
