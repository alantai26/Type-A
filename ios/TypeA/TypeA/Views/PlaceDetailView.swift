import SwiftUI

struct PlaceDetailView: View {
    let place: Place

    var body: some View {
        ScrollView {
            VStack(spacing: 28) {
                header
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
        }
        .navigationTitle(place.name)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            categoryIcon
            Text(place.name)
                .font(.system(size: 32, weight: .bold, design: .rounded))
            Text(place.category)
                .font(.callout)
                .foregroundStyle(.secondary)
            Text("\(place.latitude), \(place.longitude)")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var categoryIcon: some View {
        ZStack {
            Circle()
                .fill(Color.accentColor.opacity(0.15))
            Image(systemName: iconName(for: place.category))
                .font(.system(size: 24, weight: .medium))
                .foregroundStyle(Color.accentColor)
        }
        .frame(width: 60, height: 60)
    }

    private func iconName(for category: String) -> String {
        switch category.lowercased() {
        case "activity": return "flag.fill"
        case "restaurant": return "fork.knife"
        case "bar", "cocktail bar": return "wineglass"
        case "brewery", "beer": return "mug.fill"
        case "cafe", "coffee": return "cup.and.saucer.fill"
        case "park": return "tree.fill"
        default: return "mappin"
        }
    }
}
