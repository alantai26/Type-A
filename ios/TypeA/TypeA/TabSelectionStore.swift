import Foundation

enum AppTab: Hashable {
    case feed, plan, search, profile
}

@MainActor
@Observable
final class TabSelectionStore {
    var current: AppTab = .feed
}
