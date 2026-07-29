import Foundation
import SwiftData

@Model
final class EventItem {
    var title: String
    var notes: String
    var startDate: Date
    var endDate: Date
    var isAllDay: Bool
    var colorHex: String

    init(
        title: String,
        notes: String = "",
        startDate: Date,
        endDate: Date,
        isAllDay: Bool = false,
        colorHex: String = "A3122E"
    ) {
        self.title = title
        self.notes = notes
        self.startDate = startDate
        self.endDate = endDate
        self.isAllDay = isAllDay
        self.colorHex = colorHex
    }
}
