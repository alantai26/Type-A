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
        HStack(spacing: 10) {
            pillButton(
                label: isSaved ? "Saved" : "Save",
                icon: isSaved ? "bookmark.fill" : "bookmark",
                style: isSaved ? .outlinedAccent : .filledAccent,
                disabled: isToggling
            ) {
                Task { await toggleSave() }
            }

            pillButton(
                label: "Rate",
                icon: "star",
                style: .outlinedDisabled,
                disabled: true
            ) { }

            pillButton(
                label: "Plan",
                icon: "calendar",
                style: .outlinedDisabled,
                disabled: true
            ) { }
        }
        .frame(maxWidth: .infinity)
    }

    private enum PillStyle {
        case filledAccent
        case outlinedAccent
        case outlinedDisabled
    }

    private func pillButton(
        label: String,
        icon: String,
        style: PillStyle,
        disabled: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 13, weight: .semibold))
                Text(label)
                    .font(.system(size: 14, weight: .semibold))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 10)
            .background(pillBackground(style))
            .foregroundStyle(pillForeground(style))
            .clipShape(Capsule())
            .overlay(
                Capsule().stroke(pillBorder(style), lineWidth: 1.5)
            )
        }
        .buttonStyle(.plain)
        .disabled(disabled)
    }

    private func pillBackground(_ style: PillStyle) -> Color {
        switch style {
        case .filledAccent: return Color.accentColor
        case .outlinedAccent, .outlinedDisabled: return Color.clear
        }
    }

    private func pillForeground(_ style: PillStyle) -> Color {
        switch style {
        case .filledAccent: return .white
        case .outlinedAccent: return Color.accentColor
        case .outlinedDisabled: return .secondary
        }
    }

    private func pillBorder(_ style: PillStyle) -> Color {
        switch style {
        case .filledAccent: return Color.clear
        case .outlinedAccent: return Color.accentColor
        case .outlinedDisabled: return Color(uiColor: .separator)
        }
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
        VStack(alignment: .leading, spacing: 12) {
            Text("Friends activity")
                .font(.system(size: 18, weight: .semibold))

            if !friendsActivityLoaded {
                ProgressView()
            } else if friendsActivity.isEmpty {
                Text("No friends have rated or saved this yet")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .italic()
            } else {
                VStack(spacing: 8) {
                    ForEach(Array(friendsActivity.enumerated()), id: \.offset) { _, item in
                        friendsActivityRow(item)
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder
    private func friendsActivityRow(_ item: FriendsActivityItem) -> some View {
        switch item {
        case .rating(let r):
            activityRow(
                displayName: r.displayName,
                verb: "Rated",
                createdAt: r.createdAt,
                trailing: AnyView(scorePill(r.rating))
            )
        case .save(let s):
            activityRow(
                displayName: s.displayName,
                verb: "Saved",
                createdAt: s.createdAt,
                trailing: AnyView(
                    Image(systemName: "bookmark.fill")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(Color.accentColor)
                )
            )
        }
    }

    private func activityRow(
        displayName: String,
        verb: String,
        createdAt: Date,
        trailing: AnyView
    ) -> some View {
        HStack(spacing: 12) {
            initialsAvatar(name: displayName, size: 40)

            VStack(alignment: .leading, spacing: 2) {
                Text(displayName)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(.primary)
                Text("\(verb) · \(relativeTime(createdAt))")
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
            }

            Spacer()

            trailing
        }
        .padding(.vertical, 6)
    }

    private func initialsAvatar(name: String, size: CGFloat) -> some View {
        let initial = name.first.map { String($0).uppercased() } ?? "?"
        return Text(initial)
            .font(.system(size: size * 0.42, weight: .bold, design: .rounded))
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(Color.accentColor)
            .clipShape(Circle())
    }

    private func relativeTime(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .short
        return formatter.localizedString(for: date, relativeTo: Date())
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
                    Text(relativeTime(rating.createdAt))
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
