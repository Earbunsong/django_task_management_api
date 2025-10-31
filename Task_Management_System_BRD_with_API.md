
# **Business Requirements Document (BRD)**  
**Project:** Task Management System (Pro & Basic Subscription)  
**Technology Stack:** Django REST Framework + Flutter + PostgreSQL + Stripe + Cloudinary + Firebase

---

## **1. Project Overview**
The **Task Management System (TMS)** is a subscription-based productivity platform enabling users to manage tasks, collaborate with others, and receive notifications. It uses **Django REST Framework** for API services, **Flutter** for cross-platform UI, and **PostgreSQL** for secure data management.  

The system supports **Basic (free)** and **Pro (paid)** users, integrates **Stripe** for payments, **Cloudinary** for media uploads, and **Firebase Cloud Messaging (FCM)** for push notifications.

---

## **2. Business Objectives**
- Provide secure user authentication and subscription management.  
- Implement Stripe-based payment for Pro plan upgrades.  
- Enable CRUD task management with collaboration and attachments.  
- Support free-tier file uploads and notifications.  
- Deliver responsive Flutter UI for Android, iOS, and Web.  

---

## **3. User Roles**
| **Role** | **Description** | **Permissions** |
|-----------|-----------------|----------------|
| **Admin** | Platform operator | Manage users, disable accounts, view all payments & tasks |
| **Basic User** | Free plan | Create personal tasks, limited file uploads |
| **Pro User** | Paid plan | All Basic features + collaboration, media uploads, unlimited tasks |

---

## **4. Functional Requirements**

### **4.1 Authentication**
- Register with email verification link  
- Login using JWT token  
- Forgot password via email reset  
- Admin can disable or reactivate users  
- Roles assigned automatically on registration  

### **4.2 Payment & Subscription (Stripe)**
- User upgrades to Pro plan using Stripe Checkout  
- Monthly and annual billing  
- Stripe webhooks confirm payment success/failure  
- System updates user plan type automatically  
- Payment history accessible via user dashboard  

### **4.3 Task Management**
- CRUD (Create, Read, Update, Delete)  
- Assign tasks to other users (Pro only)  
- Track due date, priority, and status  
- Upload media files to Cloudinary  
- Filter tasks by user, due date, or project  

### **4.4 Media Uploads**
- Uses **Cloudinary Free Tier (25GB/month)**  
- Stores task-related attachments (images, PDFs, etc.)  
- Uploads from Flutter via direct upload or Django endpoint  
- Links stored as `file_url` in task record  

### **4.5 Push Notifications**
- Uses **Firebase Cloud Messaging (FCM)**  
- Triggers for:
  - Task assignment or update  
  - Payment confirmation  
  - Account status change  
- Backend integration via Firebase Admin SDK  

### **4.6 Admin Features**
- View all users and payments  
- Enable/disable user accounts  
- Manage system subscriptions  
- Export data (CSV/Excel)  

---

## **5. API Endpoint Mapping**

### **Base URL:**  
`https://api.taskmanager.com/api/v1/`

---

### **5.1 Authentication**
| **Function** | **Method** | **Endpoint** | **Description** |
|---------------|------------|---------------|----------------|
| Register User | `POST` | `/auth/register/` | Register new user and send email verification |
| Verify Email | `GET` | `/auth/verify/{token}/` | Verify account via email token |
| Login | `POST` | `/auth/login/` | Authenticate user and get JWT token |
| Logout | `POST` | `/auth/logout/` | Revoke user token |
| Forgot Password | `POST` | `/auth/forgot-password/` | Send reset password link |
| Reset Password | `POST` | `/auth/reset-password/` | Reset user password |
| Get Profile | `GET` | `/auth/profile/` | Fetch current user profile |
| Update Profile | `PUT` | `/auth/profile/` | Update user info |
| Admin Disable User | `PATCH` | `/auth/user/{id}/disable/` | Admin disables a user |

---

### **5.2 Subscription & Payment**
| **Function** | **Method** | **Endpoint** | **Description** |
|---------------|------------|---------------|----------------|
| Create Checkout Session | `POST` | `/payment/create-session/` | Create Stripe checkout session |
| Payment Success Webhook | `POST` | `/payment/webhook/` | Stripe webhook endpoint |
| Get User Subscription | `GET` | `/payment/subscription/` | Retrieve user subscription details |
| Cancel Subscription | `POST` | `/payment/cancel/` | Cancel active subscription |
| Payment History | `GET` | `/payment/history/` | Get user’s payment records |

---

### **5.3 Task Management**
| **Function** | **Method** | **Endpoint** | **Description** |
|---------------|------------|---------------|----------------|
| Get All Tasks | `GET` | `/tasks/` | List all tasks for logged-in user |
| Create Task | `POST` | `/tasks/` | Create new task |
| Get Task by ID | `GET` | `/tasks/{id}/` | Retrieve specific task |
| Update Task | `PUT` | `/tasks/{id}/` | Edit task details |
| Delete Task | `DELETE` | `/tasks/{id}/` | Delete task |
| Assign Task | `POST` | `/tasks/{id}/assign/` | Assign task to another user |
| Upload Media | `POST` | `/tasks/{id}/media/` | Upload file to Cloudinary |
| Get Task Media | `GET` | `/tasks/{id}/media/` | Retrieve media files linked to task |

---

### **5.4 Notifications**
| **Function** | **Method** | **Endpoint** | **Description** |
|---------------|------------|---------------|----------------|
| Get Notifications | `GET` | `/notifications/` | Fetch user notifications |
| Mark as Read | `PATCH` | `/notifications/{id}/read/` | Mark notification as read |
| Push FCM Token | `POST` | `/notifications/register-token/` | Register device token for FCM |

---

### **5.5 Admin Endpoints**
| **Function** | **Method** | **Endpoint** | **Description** |
|---------------|------------|---------------|----------------|
| Get All Users | `GET` | `/admin/users/` | View all users |
| Get All Payments | `GET` | `/admin/payments/` | View all payments |
| Disable User | `PATCH` | `/admin/user/{id}/disable/` | Disable user account |
| Export Users | `GET` | `/admin/export/users/` | Export user list as CSV |
| Export Payments | `GET` | `/admin/export/payments/` | Export payments as CSV |

---

## **6. Database Entities**
| **Entity** | **Key Fields** |
|-------------|----------------|
| **User** | id, email, password, role, is_verified, is_disabled, user_type |
| **Task** | id, title, description, due_date, priority, status, owner_id |
| **TaskAssignment** | id, task_id, user_id |
| **Subscription** | id, user_id, plan_type, start_date, end_date, payment_status |
| **PaymentTransaction** | id, user_id, stripe_session_id, amount, currency, status |
| **MediaFile** | id, task_id, file_url, file_type, uploaded_at |
| **Notification** | id, user_id, message, read_status, created_at |

---

## **7. Non-Functional Requirements**
- **Database:** PostgreSQL  
- **Media:** Cloudinary (Free Tier)  
- **Push Notification:** Firebase Cloud Messaging (Free)  
- **Hosting:** Render / Railway (Free Django hosting)  
- **Security:** HTTPS, JWT, CSRF protection, rate limiting  
- **Performance:** Caching, pagination, and optimized queries  

---

## **8. Free Tier Service Recommendations**
| **Service** | **Use Case** | **Free Tier Limit** | **Why Recommended** |
|--------------|---------------|--------------------|---------------------|
| **Cloudinary** | Media uploads | 25GB/month | Free, fast, easy CDN |
| **Firebase Cloud Messaging** | Push notifications | Unlimited | Reliable and free |
| **Stripe** | Payments | No monthly cost | Scalable and secure |
| **ElephantSQL / Supabase** | PostgreSQL hosting | 20–500MB | Free and simple |
| **Render / Railway** | Backend hosting | Free 500 hours/month | Easy Django deployment |

---

## **9. Future Enhancements**
- AI-based task suggestions  
- Offline sync and local caching  
- Team chat and shared workspaces  
- Multi-currency payment support  
- Analytics dashboard  

---

## **10. Final Feature Summary**
✅ JWT Auth (Email Verify, Login, Forgot Password)  
✅ Stripe Subscription Integration  
✅ Task CRUD + Assignment  
✅ Media Upload (Cloudinary)  
✅ Push Notifications (Firebase)  
✅ Admin Dashboard  
✅ PostgreSQL Database  
✅ Django REST Framework API  
✅ Flutter UI (Cross-platform)
