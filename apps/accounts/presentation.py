"""HTML presentation views for the Accounts module (auth, roles and profile).

These are the server-rendered (session-based) counterparts to the JWT REST API
(AGENTS 21) used by the browser-facing frontend. They share the same business
rules and validation as the API, but manage a Django session so that
presentation pages (``LoginRequiredMixin``, role checks) can render real data
(AGENTS 6, 8).

Views in this module:
- ``LoginView``            - session login (email + password);
- ``LogoutView``           - explicit session logout (POST);
- ``RegisterView``         - public tenant/landlord registration + auto-login;
- ``ProfileView``          - view/update the authenticated user's own profile;
- ``TenantDashboardView``  - tenant landing page with real aggregates;
- ``LandlordDashboardView``- landlord landing page with real aggregates.

Role-based access is enforced with ``RoleRequiredMixin`` and the existing
``User.is_tenant`` / ``User.is_landlord`` / ``User.is_admin`` properties so
users cannot reach pages belonging to another role (AGENTS 8).
"""
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.password_validation import validate_password
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView

from apps.apartments.models import Apartment
from apps.messaging.models import Conversation, Message
from apps.verification.models import VerificationRequest

User = get_user_model()


class LoginForm(forms.Form):
    """Session login form. Fields mirror the API ``LoginSerializer``."""

    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        password = cleaned.get("password")
        user = authenticate(email=email, password=password or "")
        if user is None:
            raise forms.ValidationError(
                "Unable to log in with the provided credentials."
            )
        if not user.is_active:
            raise forms.ValidationError("This account is inactive.")
        self.user = user
        return cleaned


class RegisterForm(forms.Form):
    """Public registration form (TENANT or LANDLORD only).

    Mirrors the API ``RegisterSerializer``: only tenant and landlord roles are
    offered, email must be unique and lowercase, and the password is checked by
    Django's built-in validators (AGENTS 19, 23).
    """

    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    full_name = forms.CharField(
        label="Full name",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
    )
    phone = forms.CharField(
        label="Phone number (optional)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "tel"}),
    )
    role = forms.ChoiceField(
        label="I am registering as",
        choices=[
            (User.Role.TENANT, "Tenant - I want to find an apartment"),
            (User.Role.LANDLORD, "Landlord - I have apartments to list"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        # Validate against Django's password policy; a weak password is
        # rejected here just as it is through the API (AGENTS 19, 23).
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        password2 = cleaned.get("password2")
        if password and password2 and password != password2:
            self.add_error("password2", "The two password fields did not match.")
        return cleaned

    def save(self):
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            full_name=self.cleaned_data["full_name"],
            phone=self.cleaned_data.get("phone", ""),
            role=self.cleaned_data["role"],
        )
        return user


class ProfileForm(forms.ModelForm):
    """Editable profile fields. Email, role and status stay read-only."""

    class Meta:
        model = User
        fields = ["full_name", "phone"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "name"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "tel"}
            ),
        }


class RoleRequiredMixin:
    """Restrict a view to a specific logged-in role (AGENTS 8)."""

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user and user.is_authenticated):
            return self.handle_no_permission(request)
        if not any(getattr(user, f"is_{role}", False) for role in self.allowed_roles):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self, request):
        return HttpResponseForbidden("Forbidden")


class LoginView(View):
    """Present the session login page and authenticate the user.

    Uses Django session login so that the rest of the presentation layer
    (which relies on ``request.user``) works unchanged. On success the user is
    redirected to their role dashboard.
    """

    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(self._home_for(request.user))
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name()}.")
            next_url = request.GET.get("next") or self._home_for(user)
            return redirect(next_url)
        return render(
            request,
            self.template_name,
            {"form": form},
            status=400,
        )

    @staticmethod
    def _home_for(user):
        if user.is_tenant:
            return reverse_lazy("tenant-dashboard")
        if user.is_landlord:
            return reverse_lazy("landlord-dashboard")
        return reverse_lazy("admin_dashboard:dashboard")


class LogoutView(View):
    """Log the user out of their session (explicit POST action)."""

    http_method_names = ["post"]

    def post(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("home")


class RegisterView(View):
    """Public registration page that also logs the new user in."""

    template_name = "accounts/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Your account was created. Welcome to Landlord-Tenant Connect.",
            )
            if user.is_landlord:
                return redirect("landlord-dashboard")
            return redirect("tenant-dashboard")
        return render(
            request,
            self.template_name,
            {"form": form},
            status=400,
        )


class ProfileView(LoginRequiredMixin, RoleRequiredMixin, View):
    """View and update the authenticated user's own profile.

    The same fields the API exposes as editable are offered here; email and
    role are displayed read-only (AGENTS 6, 21).
    """

    template_name = "accounts/profile.html"
    allowed_roles = ("tenant", "landlord")

    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(
            request,
            self.template_name,
            {"form": form, "profile_user": request.user},
        )

    def post(self, request):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect(self._after_update(request.user))
        return render(
            request,
            self.template_name,
            {"form": form, "profile_user": request.user},
            status=400,
        )

    @staticmethod
    def _after_update(user):
        if user.is_tenant:
            return reverse_lazy("tenant-dashboard")
        return reverse_lazy("landlord-dashboard")


class TenantDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Tenant landing page with real, database-backed summaries.

    Shows the tenant's search entry point, latest preferences, most recent
    recommendation feed, and message activity. Every figure is computed from
    the real database - nothing is fabricated (AGENTS 39, 40).
    """

    template_name = "accounts/tenant_dashboard.html"
    allowed_roles = ("tenant",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["browse_url"] = reverse_lazy("apartment-list")
        context["has_preference"] = False
        context["has_recommendations"] = False
        context["conversation_count"] = Conversation.objects.filter(
            tenant=user
        ).count()
        context["unread_count"] = Message.objects.filter(
            recipient=user, status=Message.Status.SENT
        ).count()

        from apps.recommendations.models import Preference, Recommendation

        preference = Preference.objects.filter(tenant=user).first()
        if preference is not None:
            context["has_preference"] = True
            context["latest_preference"] = preference
        recommendation = (
            Recommendation.objects.filter(tenant=user, items__isnull=False)
            .prefetch_related("items__apartment")
            .first()
        )
        if recommendation is not None:
            context["has_recommendations"] = True
            context["recommendation"] = recommendation
        return context


class LandlordDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Landlord landing page with real listing/verification summaries."""

    template_name = "accounts/landlord_dashboard.html"
    allowed_roles = ("landlord",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        listings = Apartment.objects.filter(landlord=user)
        context["listing_count"] = listings.count()
        context["available_count"] = listings.filter(availability=True).count()
        context["conversation_count"] = Conversation.objects.filter(
            landlord=user
        ).count()
        context["unread_count"] = Message.objects.filter(
            recipient=user, status=Message.Status.SENT
        ).count()

        verification = VerificationRequest.objects.filter(landlord=user).first()
        context["verification"] = verification
        context["verification_status"] = (
            verification.status if verification else None
        )
        context["recent_listings"] = listings.prefetch_related("images")[:6]
        context["create_url"] = reverse_lazy("apartment-create")
        return context
