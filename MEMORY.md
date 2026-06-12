# MEMORY.md - Long-Term Memory of Claw ⚡

## 🎯 CURRENT_TASK
- **Project**: `booking_system` (Location: `./Vs code progect/booking_system`)
- **Status**: Transformed from a booking system to a **Premium OLX-style Marketplace**.
- **Key Technical Changes**:
    - **Model Update**: `Room` model now includes `owner` (FK to User), `image` (ImageField), and `phone_number`.
    - **Infrastructure**: `Pillow` installed, `MEDIA_URL`/`MEDIA_ROOT` configured for image uploads.
    - **UI/UX**: 
        - Bootstrap 5 + Poppins font.
        - Premium Hero Section, hover-effect cards, and a custom **Dark Theme with Ripple Animation**.
        - `base.html` updated with a smart theme-switch and fadeIn animation.
    - **Admin Panel**: Custom Dashboard created (`admin_base.html`, `admin_dashboard.html`) with Side-Navigation and User-Staff management.
    - **Functionality**: Users can now create their own listings (`create_room`). `room_detail` now shows owner contacts instead of a booking form.
- **Next Steps**: (Paused by user).

## 🛠️ Agent Evolution
- **Installed Skill**: `agent-commons` (v1.0.3) in `/skills/agent-commons`.
- **Capability**: Now can access a global shared reasoning layer to consult, extend, and challenge AI reasoning chains for higher code quality and logic.
