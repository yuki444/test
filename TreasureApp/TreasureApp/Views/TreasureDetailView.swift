import SwiftUI

struct TreasureDetailView: View {
    @EnvironmentObject var store: TreasureStore
    @Environment(\.dismiss) var dismiss
    let item: TreasureItem
    let category: TreasureCategory

    @State private var showDeleteConfirm = false

    var body: some View {
        NavigationStack {
            ZStack {
                Color.black.ignoresSafeArea()

                VStack(spacing: 0) {
                    // Photo
                    if let img = store.loadImage(filename: item.imageFilename) {
                        Image(uiImage: img)
                            .resizable()
                            .scaledToFit()
                            .frame(maxHeight: UIScreen.main.bounds.height * 0.7)
                    } else {
                        Color.gray
                            .frame(height: 300)
                            .overlay(Image(systemName: "photo.fill").foregroundColor(.white).font(.largeTitle))
                    }

                    // Info bar
                    HStack(spacing: 12) {
                        Text(category.emoji)
                            .font(.system(size: 30))

                        VStack(alignment: .leading, spacing: 2) {
                            Text(item.subcategory)
                                .font(.system(size: 20, weight: .bold, design: .rounded))
                                .foregroundColor(.white)
                            Text(item.date, style: .date)
                                .font(.system(size: 14, design: .rounded))
                                .foregroundColor(.white.opacity(0.65))
                        }

                        Spacer()

                        // Share
                        Button { shareImage() } label: {
                            Image(systemName: "square.and.arrow.up")
                                .font(.system(size: 20))
                                .foregroundColor(.white)
                                .padding(12)
                                .background(Color.white.opacity(0.2))
                                .clipShape(Circle())
                        }

                        // Delete
                        Button { showDeleteConfirm = true } label: {
                            Image(systemName: "trash")
                                .font(.system(size: 20))
                                .foregroundColor(Color(hex: "#FF6B6B"))
                                .padding(12)
                                .background(Color.white.opacity(0.2))
                                .clipShape(Circle())
                        }
                    }
                    .padding()
                    .background(Color.black.opacity(0.6))
                }
            }
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark")
                            .foregroundColor(.white)
                            .font(.system(size: 18, weight: .semibold))
                    }
                }
            }
            .toolbarBackground(.hidden, for: .navigationBar)
        }
        .alert("けす？", isPresented: $showDeleteConfirm) {
            Button("けす", role: .destructive) {
                store.deleteItem(item)
                dismiss()
            }
            Button("やめる", role: .cancel) {}
        } message: {
            Text("このたからものを　けしていい？")
        }
    }

    private func shareImage() {
        guard let img = store.loadImage(filename: item.imageFilename) else { return }
        let av = UIActivityViewController(activityItems: [img], applicationActivities: nil)
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first?.windows.first?.rootViewController?
            .present(av, animated: true)
    }
}
