# Rappels & Agenda (iOS)

Application native SwiftUI de rappels et d'agenda, **100% locale** :
- Aucune donnée envoyée à un serveur, aucun compte requis.
- Stockage local via **SwiftData**.
- Rappels programmés via des **notifications locales** (`UserNotifications`), qui fonctionnent même hors connexion.

Ce projet est indépendant du reste du dépôt (l'app "Ordinario della Messa").

## Fonctionnalités

- **Agenda** : calendrier mensuel, création/modification/suppression d'événements (titre, date/heure ou "toute la journée", notes, couleur).
- **Rappels** : liste de rappels avec échéance, priorité (basse/moyenne/haute), notification locale programmée automatiquement, marquage "terminé".

## Prérequis

- Un **Mac** avec **Xcode 15 ou plus récent** (nécessaire pour compiler et installer sur un iPhone — impossible depuis un environnement Linux/cloud).
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) pour générer le fichier projet à partir de `project.yml` :
  ```bash
  brew install xcodegen
  ```

## Générer et ouvrir le projet

Depuis ce dossier (`ios-rappel-agenda/`) :

```bash
xcodegen generate
open RappelAgenda.xcodeproj
```

Le fichier `.xcodeproj` est généré automatiquement et n'est pas versionné (voir `.gitignore`) : relancez `xcodegen generate` après chaque modification de `project.yml`.

## Installer sur ton iPhone

1. Dans Xcode, sélectionne le projet **RappelAgenda** > onglet **Signing & Capabilities**.
2. Choisis ton **Team** (ton Apple ID personnel suffit pour un usage local — gratuit).
3. Change le **Bundle Identifier** (`com.example.rappelagenda`) pour quelque chose d'unique, par exemple `com.tonnom.rappelagenda`.
4. Branche ton iPhone en USB (ou utilise le même réseau Wi-Fi), sélectionne-le comme destination, puis clique sur **Run** (▶).
5. Sur l'iPhone, si demandé, autorise l'app dans **Réglages > Général > VPN et gestion de l'appareil**.
6. Accepte la demande d'autorisation de notifications au premier lancement (nécessaire pour que les rappels s'affichent).

## Structure du projet

```
ios-rappel-agenda/
  project.yml                        # définition XcodeGen du projet
  Sources/
    RappelAgendaApp.swift            # point d'entrée
    Models/
      EventItem.swift                # modèle SwiftData : événement d'agenda
      ReminderItem.swift             # modèle SwiftData : rappel
    Notifications/
      NotificationManager.swift      # programmation des notifications locales
    Extensions/
      Color+Hex.swift
    Views/
      ContentView.swift              # TabView Agenda / Rappels
      Agenda/
        AgendaView.swift
        MonthCalendarView.swift
        AddEditEventView.swift
      Reminders/
        ReminderListView.swift
        AddEditReminderView.swift
  Resources/
    Assets.xcassets/                 # icône d'app (placeholder) + couleur d'accent
```

## Limites connues / pistes d'amélioration

- L'icône d'app est un emplacement vide (`AppIcon.appiconset`) — ajoute une image 1024×1024 dans Xcode si tu veux une vraie icône.
- Pas de synchronisation iCloud/multi-appareils par choix (application volontairement locale). Pour ajouter une synchro plus tard, `SwiftData` peut être branché sur **CloudKit** sans changer le modèle de données.
- Pas d'intégration avec l'app Calendrier/Rappels d'Apple (EventKit) : les données restent propres à cette app. Cela peut être ajouté si tu veux exporter/importer avec les apps système.
