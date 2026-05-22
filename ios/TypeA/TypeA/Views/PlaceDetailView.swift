import SwiftUI

struct PlaceDetailView: View {
    let place: Place
    @State private var myRating: PlaceRating?
    @State private var myRatingLoaded = false
    @State private var friendsActivity: [FriendsActivityItem] = []
    @State private var friendsActivityLoaded = false
    @State private var isSaved: Bool
    @State private var isToggling = false

    init(place: Place) {
        self.place = place
        self._isSaved = State(initialValue: place.isSaved)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 28) {
                header
                myRatingSection
                friendsActivitySection
                actionsSection
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
        }
        .navigationTitle(place.name)
        .navigationBarTitleDisplayMode(.inline)
        .task {
            do {
                let rating: PlaceRating? = try await APIClient.shared.request(
                    "/places/\(place.placeId)/my_rating"
                )
                myRating = rating
            } catch {
                print("PlaceDetailView: failed to load my_rating - \(error)")
            }
            myRatingLoaded = true

            do {
                let activity: [FriendsActivityItem] = try await APIClient.shared.request(
                    "/places/\(place.placeId)/friends_activity"
                )
                friendsActivity = activity
            } catch {
                print("PlaceDetailView: failed to load friends_activity - \(error)")
            }
            friendsActivityLoaded = true
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            categoryIcon
            Text(place.name)
                .font(.system(size: 32, weight: .bold, design: .rounded))
            Text(place.category)
                .font(.callout)
                .foregroundStyle(.secondary)
            if place.latitude != 0 || place.longitude != 0 {
                Text("\(place.latitude), \(place.longitude)")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
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

    private var actionsSection: some View {
        HStack(spacing: 16) {
            Button(isSaved ? "Unsave" : "Save") {
                Task { await toggleSave() }
            }
            .disabled(isToggling)

            Button("Rate") { }
                .disabled(true)

            Button("Plan") { }
                .disabled(true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func toggleSave() async {
        isToggling = true
        defer { isToggling = false }
        do {
            if isSaved {
                try await APIClient.shared.requestVoid(
                    "/saved_places/\(place.placeId)", method: "DELETE"
                )
            } else {
                try await APIClient.shared.requestVoid(
                    "/saved_places/\(place.placeId)", method: "POST"
                )
            }
            isSaved.toggle()
        } catch {
            print("PlaceDetailView: toggle save failed - \(error)")
        }
    }

    private var friendsActivitySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Friends activity")
                .font(.headline)
            if !friendsActivityLoaded {
                ProgressView()
            } else if friendsActivity.isEmpty {
                Text("No friends activity yet")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(Array(friendsActivity.enumerated()), id: \.offset) { _, item in
                    switch item {
                    case .rating(let r):
                        Text("\(r.displayName) rated this \(String(format: "%.1f", r.rating))")
                    case .save(let s):
                        Text("\(s.displayName) saved this")
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var myRatingSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Your rating")
                .font(.system(size: 18, weight: .semibold))

            if !myRatingLoaded {
                ProgressView()
            } else if let rating = myRating {
                HStack(spacing: 12) {
                    scorePill(rating.rating)
                    Text("You rated this \(String(format: "%.1f", rating.rating))")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
            } else {
                Text("You haven't rated this yet")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .italic()
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
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

    private func scorePill(_ rating: Double) -> some View {
        let colors = scoreColors(for: rating)
        return Text(String(format: "%.1f", rating))
            .font(.system(size: 15, weight: .bold, design: .rounded))
            .foregroundStyle(colors.text)
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(colors.bg)
            .clipShape(Capsule())
    }

    private func scoreColors(for rating: Double) -> (bg: Color, text: Color) {
        if rating >= 6.7 {
            return (
                Color(red: 0.91, green: 0.97, blue: 0.93),
                Color(red: 0.12, green: 0.54, blue: 0.25)
            )
        } else if rating >= 3.4 {
            return (
                Color(red: 1.00, green: 0.96, blue: 0.90),
                Color(red: 0.55, green: 0.41, blue: 0.08)
            )
        } else {
            return (
                Color(red: 0.99, green: 0.93, blue: 0.93),
                Color(red: 0.78, green: 0.16, blue: 0.16)
            )
        }
    }
}
