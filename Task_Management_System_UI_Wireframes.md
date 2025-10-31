
# Task Management System – Flutter UI Wireframes

## **1. Overview**
The **Task Management System (TMS)** app is built with **Flutter 3.x**, following **Material Design 3** principles.  
It supports **Android, iOS, and Web**, with light/dark theme switching, and integrates tightly with the **Django REST API** backend.

The application includes a navigation drawer and bottom navigation bar for a modern and consistent UI/UX experience.

---

## **2. App Navigation Flow**
```
Splash → Login → Register → Dashboard → Task Detail → Edit Task → Payment → Notifications → Profile → (Admin Dashboard if Admin)
```

**Navigation Type:**  
- `MaterialApp` with named routes  
- Auth Guard middleware for protected pages  
- Drawer Navigation for main pages  
- Bottom Navigation Bar for quick access (Dashboard, Tasks, Notifications, Profile)

---

## **3. Wireframes by Screen**

### **3.1 Splash Screen**
- Shows app logo and tagline.
- Automatically redirects to Login if not authenticated, else Dashboard.

```
+--------------------------------------+
|              Logo                    |
|     "Task Management System"         |
|         [Loading Spinner]            |
+--------------------------------------+
```

---

### **3.2 Login Screen**
```
+--------------------------------------+
|          [Logo / App Title]          |
| Email: [______________]              |
| Password: [______________]           |
| [ Login ]                            |
| Forgot Password? [Link]              |
| Register Here [Link]                 |
+--------------------------------------+
```
- Calls `/auth/login/`
- Stores JWT token securely with `flutter_secure_storage`
- On success → navigate to Dashboard.

---

### **3.3 Register Screen**
```
+--------------------------------------+
| Name: [______________]               |
| Email: [______________]              |
| Password: [______________]           |
| Confirm Password: [______________]   |
| [ Register ]                         |
| Already have an account? [Login]     |
+--------------------------------------+
```
- Calls `/auth/register/`
- On success → Email verification message.

---

### **3.4 Dashboard Screen**
```
+--------------------------------------+
| AppBar: "Dashboard"   [🔔]           |
| Tabs: [All] [Pending] [Completed]   |
|                                      |
| [Task Card] Title, Status, Due Date  |
| [Task Card] ...                      |
|                                      |
| [+] Floating Add Task Button         |
+--------------------------------------+
Bottom Nav: [🏠 Dashboard] [📋 Tasks] [💳 Payment] [👤 Profile]
```
- Fetches tasks via `/tasks/`
- Floating button → `/tasks/` (POST new task)
- Displays filter chips and progress indicators.

---

### **3.5 Task Detail Screen**
```
+--------------------------------------+
| [< Back]   Task Title   [⋮ Menu]     |
|--------------------------------------|
| Description: [Text area]             |
| Due Date: [YYYY-MM-DD]               |
| Priority: [Low | Medium | High]      |
| Status: [Pending | In Progress]      |
|--------------------------------------|
| [ Attach File 📎 ] [ Assign User 👥 ] |
| [ Save ] [ Delete ]                  |
+--------------------------------------+
```
- Edit/Delete → `/tasks/{id}/`  
- Upload → `/tasks/{id}/media/`  
- Assign collaborator (Pro only) → `/tasks/{id}/assign/`  

---

### **3.6 Payment / Subscription Screen**
```
+--------------------------------------+
| AppBar: "Subscription Plan"          |
| Current Plan: [ Basic | Pro ]        |
| [ Upgrade to Pro 💳 ]                |
|--------------------------------------|
| Payment History                      |
| - Stripe: $9.99/month on Jan 10      |
| - Stripe: $9.99/month on Feb 10      |
+--------------------------------------+
```
- `/payment/create-session/` → opens Stripe Checkout  
- `/payment/subscription/` → show active plan info  
- `/payment/history/` → show past transactions  

---

### **3.7 Notification Screen**
```
+--------------------------------------+
| AppBar: "Notifications"              |
|--------------------------------------|
| 🔔 [Task Updated] “Rain Data Sync”   |
| 🧾 [Payment Successful] $9.99 Plan   |
| ✅ [Task Completed]                  |
+--------------------------------------+
```
- Lists from `/notifications/`  
- Tap → mark as read `/notifications/{id}/read/`  
- Realtime updates from Firebase Cloud Messaging (FCM)

---

### **3.8 Profile Screen**
```
+--------------------------------------+
| [User Avatar]                        |
| Name: John Doe                       |
| Email: john@demo.com                 |
|--------------------------------------|
| [ Edit Profile ]                     |
| [ Logout ]                           |
|--------------------------------------|
| Version 1.0.0                        |
+--------------------------------------+
```
- Fetches `/auth/profile/`
- Logout clears secure storage.

---

### **3.9 Admin Dashboard**
```
+--------------------------------------+
| AppBar: "Admin Panel"                |
| Tabs: [Users] [Payments]             |
|--------------------------------------|
| [User List] Disable/Enable Buttons   |
| [Export CSV]                         |
+--------------------------------------+
```
- `/admin/users/`, `/admin/payments/`  
- Export and user management tools.

---

## **4. Navigation & Routing Structure**
Example Flutter route setup:
```dart
final Map<String, WidgetBuilder> routes = {
  '/login': (context) => LoginScreen(),
  '/register': (context) => RegisterScreen(),
  '/dashboard': (context) => DashboardScreen(),
  '/task_detail': (context) => TaskDetailScreen(),
  '/payment': (context) => PaymentScreen(),
  '/notifications': (context) => NotificationScreen(),
  '/profile': (context) => ProfileScreen(),
  '/admin': (context) => AdminDashboard(),
};
```
- Auth guard checks stored token before navigating to protected routes.

---

## **5. Theming & UX Guidelines**
- Use **Material Design 3** components.  
- **Colors:**
  - Primary: `#1976D2` (Blue)
  - Secondary: `#FFC107` (Amber)
  - Background: Light/Dark adaptive  
- **Fonts:** Inter / Roboto  
- **Icons:** Material Icons / Lucide  
- Support responsive design (tablet + mobile)
- Dark Mode supported automatically.

---

## **6. Future Enhancements**
- Add charts (task completion rate)  
- Voice command support (speech-to-text)  
- Offline mode (local SQLite sync)  
- Custom themes per user plan  

---

## **7. Flutter Project Structure & Key Files**
A recommended folder/file layout to implement the above wireframes:

```text path=null start=null
lib/
  main.dart
  app.dart
  core/
    env.dart
    config.dart
    routes.dart
    dio_client.dart        // HTTP client (dio) with interceptors for JWT
    secure_storage.dart    // wrapper around flutter_secure_storage
    theme/
      app_theme.dart
  common/
    widgets/
      app_button.dart
      app_text_field.dart
      empty_state.dart
      error_view.dart
  features/
    auth/
      data/models/user.dart
      data/dto/login_request.dart
      data/dto/register_request.dart
      data/auth_api.dart
      data/auth_repository.dart
      presentation/screens/login_screen.dart
      presentation/screens/register_screen.dart
      presentation/providers/auth_provider.dart   // or bloc/cubit
    tasks/
      data/models/task.dart
      data/dto/task_request.dart
      data/task_api.dart
      data/task_repository.dart
      presentation/screens/dashboard_screen.dart
      presentation/screens/task_detail_screen.dart
      presentation/screens/edit_task_screen.dart
      presentation/widgets/task_card.dart
      presentation/widgets/task_filters.dart
      presentation/providers/task_provider.dart
    payments/
      data/payment_api.dart
      data/payment_repository.dart
      presentation/screens/payment_screen.dart
      presentation/widgets/payment_history_list.dart
    notifications/
      data/notification_api.dart
      data/notification_repository.dart
      presentation/screens/notification_screen.dart
      services/push_notifications.dart   // FCM integration
    profile/
      data/profile_api.dart
      data/profile_repository.dart
      presentation/screens/profile_screen.dart
      presentation/screens/edit_profile_screen.dart
    admin/
      data/admin_api.dart
      data/admin_repository.dart
      presentation/screens/admin_dashboard.dart
      presentation/widgets/user_list.dart
assets/
  icons/
  images/
  fonts/
```

Notes:
- Replace "provider" with Riverpod/Bloc as preferred; structure still applies.
- Keep networking, repositories, and presentation separated per feature.

---

## **8. API Client & Endpoints (Django REST)**
Centralize API config and endpoints so screens stay clean.

```dart path=null start=null
// core/config.dart
class ApiConfig {
  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://your-domain.com/api',
  );
}

// core/dio_client.dart
import 'package:dio/dio.dart';

class DioClient {
  DioClient(this._tokenGetter)
      : dio = Dio(BaseOptions(baseUrl: ApiConfig.baseUrl)) {
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _tokenGetter();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
  }

  final Future<String?> Function() _tokenGetter;
  final Dio dio;
}
```

Key endpoints mapping:
- Auth: `/auth/login/`, `/auth/register/`, `/auth/profile/`
- Tasks: `/tasks/`, `/tasks/{id}/`, `/tasks/{id}/media/`, `/tasks/{id}/assign/`
- Payments: `/payment/create-session/`, `/payment/subscription/`, `/payment/history/`
- Notifications: `/notifications/`, `/notifications/{id}/read/`
- Admin: `/admin/users/`, `/admin/payments/`

---

## **9. Screens & Widgets To Create (Checklist)**
- Splash: `main.dart` boot, token check, route to Login/Dashboard
- Auth:
  - `features/auth/presentation/screens/login_screen.dart`
  - `features/auth/presentation/screens/register_screen.dart`
- Dashboard/Tasks:
  - `features/tasks/presentation/screens/dashboard_screen.dart`
  - `features/tasks/presentation/widgets/task_card.dart`
  - `features/tasks/presentation/widgets/task_filters.dart`
  - `features/tasks/presentation/screens/task_detail_screen.dart`
  - `features/tasks/presentation/screens/edit_task_screen.dart`
- Payments:
  - `features/payments/presentation/screens/payment_screen.dart`
  - `features/payments/presentation/widgets/payment_history_list.dart`
- Notifications:
  - `features/notifications/presentation/screens/notification_screen.dart`
  - `features/notifications/services/push_notifications.dart`
- Profile:
  - `features/profile/presentation/screens/profile_screen.dart`
  - `features/profile/presentation/screens/edit_profile_screen.dart`
- Admin:
  - `features/admin/presentation/screens/admin_dashboard.dart`
  - `features/admin/presentation/widgets/user_list.dart`
- Common:
  - `common/widgets/app_button.dart`, `app_text_field.dart`, `empty_state.dart`, `error_view.dart`

---

## **10. Routing & Guards (Files)**
- `core/routes.dart`: central route names + generator
- `app.dart`: `MaterialApp.router` with theme + auth guard

```dart path=null start=null
class Routes {
  static const login = '/login';
  static const register = '/register';
  static const dashboard = '/dashboard';
  static const taskDetail = '/task_detail';
  static const payment = '/payment';
  static const notifications = '/notifications';
  static const profile = '/profile';
  static const admin = '/admin';
}
```

---

## **11. Theming & Assets (Files)**
- `core/theme/app_theme.dart`: Material 3 light/dark themes
- Add assets to `pubspec.yaml` under `assets:` and `fonts:`

```yaml path=null start=null
flutter:
  uses-material-design: true
  assets:
    - assets/icons/
    - assets/images/
  fonts:
    - family: Inter
      fonts:
        - asset: assets/fonts/Inter-Regular.ttf
        - asset: assets/fonts/Inter-Bold.ttf
          weight: 700
```
