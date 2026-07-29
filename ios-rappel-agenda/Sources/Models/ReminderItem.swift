import Foundation
import SwiftData

enum Priority: Int, Codable, CaseIterable, Identifiable {
    case low = 0
    case medium = 1
    case high = 2

    var id: Int { rawValue }

    var label: String {
        switch self {
        case .low: return "Basse"
        case .medium: return "Moyenne"
        case .high: return "Haute"
        }
    }
}

@Model
final class ReminderItem {
    var title: String
    var notes: String
    var dueDate: Date
    var isCompleted: Bool
    var priorityRawValue: Int
    var notificationID: String

    var priority: Priority {
        get { Priority(rawValue: priorityRawValue) ?? .medium }
        set { priorityRawValue = newValue.rawValue }
    }

    init(
        title: String,
        notes: String = "",
        dueDate: Date,
        priority: Priority = .medium,
        isCompleted: Bool = false
    ) {
        self.title = title
        self.notes = notes
        self.dueDate = dueDate
        self.priorityRawValue = priority.rawValue
        self.isCompleted = isCompleted
        self.notificationID = UUID().uuidString
    }
}
