"""Administrator dashboard presentation views (Phase 6, Sprints 6.1-6.2).

Sprint 6.1 delivered the **Administrator dashboard** (SYSTEM_REQUIREMENTS §40,
FR-005; AGENTS 42): admin-only HTML pages providing a system overview and
management entry points:

- ``DashboardView``           - system overview with cross-module counts;
- ``UserManagementView``      - user management overview (list + role filter);
- ``LandlordManagementView``  - landlord management overview (with verification);
- ``ApartmentManagementView`` - apartment management overview (all listings);
- ``VerificationOverviewView`` - verification workflow overview (by status).

Sprint 6.2 completes the **administrative workflows** behind those pages:

- ``UserStatusActionView``    - user status management (activate/deactivate);
- ``ApartmentModerationView`` - apartment moderation (hide/unhide a listing);
- ``VerificationActionView``  - verification administration (approve/reject);
- ``ReportsView``             - administrative reports (system aggregates).

Every view is guarded by ``AdminOnlyMixin`` so only the ADMINISTRATOR role can
reach them (AGENTS 8, 19); landlords, tenants and anonymous users are blocked
with a 403. State changes reuse the model logic (``User.is_active``,
``Apartment.availability``, ``VerificationRequest.approve/reject``) so there is
no duplicated business logic in the presentation layer (AGENTS 6).
"""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView

from apps.apartments.models import Apartment
from apps.messaging.models import Conversation, Message
from apps.verification.models import VerificationRequest

User = get_user_model()


class AdminOnlyMixin:
    """Restrict a view to authenticated ADMINISTRATOR users.

    Overrides ``dispatch`` so a non-admin (or anonymous) user receives a 403
    rather than reaching the page (AGENTS 8, 19).
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user and user.is_authenticated and user.is_admin):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(AdminOnlyMixin, TemplateView):
    """System overview with tallies across users, apartments and verification.

    Provides the administrative "system overview" (FR-005): counts of users by
    role, active status, apartments, availability, verification requests by
    status, and messaging volume. No fabricated statistics are used (AGENTS 39);
    every figure is an aggregate over the real database.
    """

    template_name = "admin_dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        role_counts = dict(
            User.objects.values_list("role").annotate(total=Count("id"))
        )
        verification_counts = dict(
            VerificationRequest.objects.values_list("status").annotate(
                total=Count("id")
            )
        )
        context.update(
            {
                "total_users": User.objects.count(),
                "active_users": User.objects.filter(is_active=True).count(),
                "tenant_count": role_counts.get(User.Role.TENANT, 0),
                "landlord_count": role_counts.get(User.Role.LANDLORD, 0),
                "admin_count": role_counts.get(User.Role.ADMIN, 0),
                "total_apartments": Apartment.objects.count(),
                "available_apartments": Apartment.objects.filter(
                    availability=True
                ).count(),
                "verification_pending": verification_counts.get(
                    VerificationRequest.Status.PENDING, 0
                ),
                "verification_approved": verification_counts.get(
                    VerificationRequest.Status.APPROVED, 0
                ),
                "verification_rejected": verification_counts.get(
                    VerificationRequest.Status.REJECTED, 0
                ),
                "total_conversations": Conversation.objects.count(),
                "total_messages": Message.objects.count(),
                "active_landlords": (
                    User.objects.filter(role=User.Role.LANDLORD, is_active=True)
                    .count()
                ),
            }
        )
        return context


class UserManagementView(AdminOnlyMixin, ListView):
    """User management overview: list users with a role filter.

    Supports a ``role`` query parameter (TENANT / LANDLORD / ADMIN) so an
    administrator can focus on a single role. Shows identity, role, active
    status and join date.
    """

    template_name = "admin_dashboard/users.html"
    context_object_name = "users"
    paginate_by = 50

    def get_queryset(self):
        queryset = User.objects.all().order_by("-date_joined")
        role = self.request.GET.get("role")
        if role in {User.Role.TENANT, User.Role.LANDLORD, User.Role.ADMIN}:
            queryset = queryset.filter(role=role)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = self.request.GET.get("role", "")
        context["role_choices"] = User.Role.choices
        return context


class LandlordManagementView(AdminOnlyMixin, ListView):
    """Landlord management overview: list landlord accounts.

    Shows each landlord together with their verification status (a landlord is
    verified once any APPROVED verification request exists). Review actions are
    handled in Sprint 6.2.
    """

    template_name = "admin_dashboard/landlords.html"
    context_object_name = "landlords"
    paginate_by = 50

    def get_queryset(self):
        return (
            User.objects.filter(role=User.Role.LANDLORD)
            .prefetch_related("verification_requests")
            .order_by("-date_joined")
        )


class ApartmentManagementView(AdminOnlyMixin, ListView):
    """Apartment management overview: list all listings for an administrator.

    Mirrors the landlord's ``MyApartmentsView`` but always lists every listing
    (not only those owned by the current user) with availability and the owning
    landlord visible.
    """

    template_name = "admin_dashboard/apartments.html"
    context_object_name = "apartments"
    paginate_by = 50

    def get_queryset(self):
        return Apartment.objects.all().select_related("landlord").prefetch_related(
            "images"
        ).order_by("-created_at")


class VerificationOverviewView(AdminOnlyMixin, ListView):
    """Verification workflow overview grouped by status.

    Filters by a ``status`` query parameter (defaults to PENDING so the most
    urgent work is shown first). Review actions are handled in Sprint 6.2.
    """

    template_name = "admin_dashboard/verifications.html"
    context_object_name = "verifications"
    paginate_by = 50

    def get_queryset(self):
        status = self.request.GET.get("status") or VerificationRequest.Status.PENDING
        return (
            VerificationRequest.objects.filter(status=status)
            .select_related("landlord")
            .order_by("-submitted_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get(
            "status", VerificationRequest.Status.PENDING
        )
        context["status_choices"] = VerificationRequest.Status.choices
        return context


class UserStatusActionView(AdminOnlyMixin, TemplateView):
    """Toggle an account's active status (user status management).

    ``POST`` flips ``is_active`` for the target user so an administrator can
    enable or disable an account (FR-005 "manage users"). Disabling prevents
    the user from authenticating while preserving their data. The target is a
    normal (non-admin) account; administrators are never deactivated through
    this action.
    """

    @method_decorator(require_POST)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.is_admin:
            messages.error(request, "Administrator accounts cannot be toggled here.")
            return redirect("admin_dashboard:users")
        user.is_active = not user.is_active
        user.save(update_fields=["is_active", "updated_at"])
        state = "enabled" if user.is_active else "disabled"
        messages.success(request, f"User {user.email} {state}.")
        return redirect("admin_dashboard:users")


class ApartmentModerationView(AdminOnlyMixin, TemplateView):
    """Moderate an apartment listing (set availability).

    ``POST`` hides or unhides a listing by toggling ``availability``. Hiding
    (unavailable) removes it from tenant search and recommendation candidates
    while preserving the record, which safely covers the FR-005 "remove
    inappropriate listings" requirement without destructive deletion.
    """

    @method_decorator(require_POST)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        apartment = get_object_or_404(Apartment, pk=pk)
        apartment.availability = not apartment.availability
        apartment.save(update_fields=["availability", "updated_at"])
        state = "made available" if apartment.availability else "hidden (unavailable)"
        messages.success(request, f"Listing '{apartment.title}' {state}.")
        return redirect("admin_dashboard:apartments")


class VerificationActionView(AdminOnlyMixin, TemplateView):
    """Review a verification request (verification administration).

    ``POST`` approves or rejects a pending request, delegating to the model's
    ``approve`` / ``reject`` methods so the persisted state and timestamps stay
    consistent with the API workflow (Sprint 3.2). Rejection accepts an optional
    ``remarks`` field. An already-reviewed request cannot be re-reviewed.
    """

    @method_decorator(require_POST)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        verification = get_object_or_404(VerificationRequest, pk=pk)
        action = request.POST.get("action")
        if not verification.is_pending:
            messages.error(request, "Only pending requests can be reviewed.")
            return redirect("admin_dashboard:verifications")

        if action == "approve":
            verification.approve(admin=request.user)
            messages.success(request, "Verification approved.")
        elif action == "reject":
            remarks = request.POST.get("remarks", "").strip()
            verification.reject(admin=request.user, remarks=remarks)
            messages.success(request, "Verification rejected.")
        else:
            messages.error(request, "Unknown review action.")
        return redirect("admin_dashboard:verifications")


class ReportsView(AdminOnlyMixin, TemplateView):
    """Administrative reports page (FR-005 "access administrative reports").

    Aggregates live database figures into management reports: user breakdown by
    role, listing availability, verification funnel and messaging volume. Every
    number is computed from the real database; nothing is fabricated (AGENTS
    39).
    """

    template_name = "admin_dashboard/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_counts = dict(
            User.objects.values_list("role").annotate(total=Count("id"))
        )
        verification_counts = dict(
            VerificationRequest.objects.values_list("status").annotate(
                total=Count("id")
            )
        )
        context.update(
            {
                "role_counts": {
                    User.Role.TENANT: role_counts.get(User.Role.TENANT, 0),
                    User.Role.LANDLORD: role_counts.get(User.Role.LANDLORD, 0),
                    User.Role.ADMIN: role_counts.get(User.Role.ADMIN, 0),
                },
                "active_users": User.objects.filter(is_active=True).count(),
                "inactive_users": User.objects.filter(is_active=False).count(),
                "apartments_total": Apartment.objects.count(),
                "apartments_available": Apartment.objects.filter(
                    availability=True
                ).count(),
                "apartments_hidden": Apartment.objects.filter(
                    availability=False
                ).count(),
                "verification_counts": {
                    VerificationRequest.Status.PENDING: verification_counts.get(
                        VerificationRequest.Status.PENDING, 0
                    ),
                    VerificationRequest.Status.APPROVED: verification_counts.get(
                        VerificationRequest.Status.APPROVED, 0
                    ),
                    VerificationRequest.Status.REJECTED: verification_counts.get(
                        VerificationRequest.Status.REJECTED, 0
                    ),
                },
                "conversation_count": Conversation.objects.count(),
                "message_count": Message.objects.count(),
            }
        )
        return context
