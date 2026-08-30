"""Administrator dashboard presentation views (Phase 6, Sprint 6.1).

Sprint 6.1 delivers the **Administrator dashboard** (SYSTEM_REQUIREMENTS §40,
FR-005; AGENTS 42). Admin-only HTML pages provide a system overview and
management entry points:

- ``DashboardView``           - system overview with cross-module counts;
- ``UserManagementView``      - user management overview (list + role filter);
- ``LandlordManagementView``  - landlord management overview (with verification);
- ``ApartmentManagementView`` - apartment management overview (all listings);
- ``VerificationOverviewView`` - verification workflow overview (by status).

These are presentation-side overviews; the granular moderation actions
(approve/reject, delete, status changes, reports) belong to Sprint 6.2. Every
view is guarded by ``AdminOnlyMixin`` so only the ADMINISTRATOR role can reach
them (AGENTS 8, 19); landlords and tenants are blocked with a 403.
"""
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpResponseForbidden
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
