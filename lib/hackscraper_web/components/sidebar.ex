defmodule HackScraperWeb.Components.Sidebar do
  @moduledoc """
  Sidebar navigation component with responsive design and collapsible desktop mode.
  Shows different menu items based on user authentication and admin status.
  """
  use HackScraperWeb, :html

  @doc """
  Renders the main sidebar navigation.
  """
  attr :current_user, :any, default: nil
  attr :class, :string, default: ""
  attr :dev_mode, :boolean, default: Application.compile_env(:hackscraper, :dev_routes)

  def sidebar(assigns) do
    ~H"""
    <!-- backdrop for mobile -->
    <div
      class="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
      id="sidebar-backdrop"
      style="display: none;"
      phx-click={
        JS.add_class("-translate-x-full", to: "#sidebar")
        |> JS.hide(to: "#sidebar-backdrop")
        |> JS.show(to: "#mobile-menu-button")
      }
    >
    </div>

    <div
      id="sidebar"
      class={"#{@class} fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform -translate-x-full lg:translate-x-0 lg:static lg:inset-0 transition-all duration-300 ease-in-out lg:w-64 text-nowrap"}
      data-collapsed="false"
    >
      <div class="flex justify-center items-center h-16 px-4 border-b border-gray-700">
        <!-- Desktop collapse button -->
        <button
          class="hidden lg:block text-gray-400 hover:text-white flex-shrink-0"
          id="collapse-btn"
          onclick="toggleSidebar()"
        >
          <.icon name="hero-bars-3" class="w-5 h-5" />
        </button>

        <!-- Mobile close button -->
        <button
          class="lg:hidden text-gray-400 hover:text-white relative"
          phx-click={
            JS.add_class("-translate-x-full", to: "#sidebar")
            |> JS.hide(to: "#sidebar-backdrop")
            |> JS.show(to: "#mobile-menu-button")
          }
        >
          <.icon name="hero-x-mark" class="w-6 h-6" />
          <span class="absolute inset-[-0.75em]"></span>
        </button>

        <div class="flex flex-1 justify-center sidebar-text">
          <.link href={~p"/"} class="flex items-center space-x-2">
            <img src={~p"/images/logo.png"} width="32" height="32" alt="HackScraper" />
            <span class="text-xl font-semibold">HackScraper</span>
          </.link>
        </div>
      </div>

      <nav class="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        <div class="space-y-1">
          <h3 class="px-3 text-xs font-medium text-gray-400 uppercase tracking-wider mb-3 sidebar-text">
            Discover
          </h3>

          <.nav_link navigate={~p"/hackathons"} icon="hero-calendar-days">
            <span class="sidebar-text">Hackathons</span>
          </.nav_link>

          <.nav_link navigate={~p"/series"} icon="hero-rectangle-stack">
            <span class="sidebar-text">Series</span>
          </.nav_link>

          <%= if  @current_user do %>
            <.nav_link navigate={~p"/suggestions"} icon="hero-pencil-square">
              <span class="sidebar-text">Suggestions</span>
            </.nav_link>
          <% end %>
        </div>

        <%= if HackScraper.Accounts.can_do?(@current_user, :mod) do %>
          <div class="space-y-1 pt-6">
            <h3 class="px-3 text-xs font-medium text-gray-400 uppercase tracking-wider mb-3 sidebar-text">
              Administration
            </h3>

            <.nav_link navigate={~p"/users"} icon="hero-users">
              <span class="sidebar-text">Users</span>
            </.nav_link>

            <%= if HackScraper.Accounts.can_do?(@current_user, :admin) do %>
              <.nav_link navigate={~p"/scrapers"} icon="hero-clock">
                <span class="sidebar-text">Scrapers</span>
              </.nav_link>

              <.nav_link href={~p"/oban"} icon="hero-wrench-screwdriver">
                <span class="sidebar-text">Jobs (Oban)</span>
              </.nav_link>

              <.nav_link navigate={~p"/dashboard"} icon="hero-chart-bar">
                <span class="sidebar-text">Dashboard</span>
              </.nav_link>

              <.nav_link :if={@dev_mode} href="/mailbox" icon="hero-envelope">
                <span class="sidebar-text">Mailbox</span>
              </.nav_link>
            <% end %>
          </div>
        <% end %>

        <%= if @current_user do %>
          <div class="space-y-3 pt-6">
            <h3 class="px-3 text-xs font-medium text-gray-400 uppercase tracking-wider mb-3 sidebar-text">
              Account
            </h3>

            <.nav_link href={~p"/user/settings"} icon="hero-cog-6-tooth">
              <div class="flex-1 min-w-0 sidebar-text">
                <span>{@current_user.name}</span>
                <p class="text-xs text-gray-400 truncate">{@current_user.email}</p>
              </div>
            </.nav_link>
            <.link
              href={~p"/user/log_out"}
              method="delete"
              class="nav-link flex items-center px-3 py-2 gap-3 text-sm font-medium text-white bg-red-700 hover:bg-red-800 rounded-md transition-colors justify-center"
            >
              <.icon name="hero-arrow-right-on-rectangle" class="w-5 h-5 flex-shrink-0" />
              <span class="sidebar-text">Log out</span>
            </.link>
          </div>
        <% else %>
          <div class="space-y-4 pt-6">
            <h3 class="px-3 text-xs font-medium text-gray-400 uppercase tracking-wider mb-3 sidebar-text">
              Account
            </h3>

            <.link
              navigate={~p"/user/log_in"}
              class="nav-link flex items-center px-3 py-2 gap-3 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 rounded-md transition-colors justify-center"
            >
              <.icon name="hero-arrow-left-on-rectangle" class="w-5 h-5 flex-shrink-0" />
              <span class="sidebar-text">Log in</span>
            </.link>
            <%= if HackScraper.Accounts.registration_enabled?() do %>
              <.link
                navigate={~p"/user/register"}
                class="nav-link flex items-center px-3 py-2 gap-3 text-sm font-medium text-white bg-zinc-600 hover:bg-zinc-700 rounded-md transition-colors justify-center"
              >
                <.icon name="hero-user-plus" class="w-5 h-5 flex-shrink-0" />
                <span class="sidebar-text">Register</span>
              </.link>
            <% end %>
          </div>
        <% end %>
      </nav>
    </div>

    <style>
      /* Sidebar responsive styles */
      @media (min-width: 1024px) {
        #sidebar[data-collapsed="true"] {
            width: 4rem !important;
        }

        #sidebar[data-collapsed="true"] .sidebar-text {
            display: none;
        }

        #sidebar[data-collapsed="true"] .nav-link {
            justify-content: center;
        }

        /* Adjust main content when sidebar is collapsed */
        body:has(#sidebar[data-collapsed="true"]) main {
            grid-template-columns: 4rem 1fr;
        }
      }
    </style>

    <script>
      function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const isCollapsed = sidebar.getAttribute('data-collapsed') === 'true';

        if (isCollapsed) {
          sidebar.setAttribute('data-collapsed', 'false');
          sidebar.classList.remove('lg:w-16');
          sidebar.classList.add('lg:w-64');
        } else {
          sidebar.setAttribute('data-collapsed', 'true');
          sidebar.classList.remove('lg:w-64');
          sidebar.classList.add('lg:w-16');
        }
      }
    </script>
    """
  end

  # Renders a navigation link with icon.
  attr :navigate, :string, default: nil
  attr :href, :string, default: nil
  attr :icon, :string, required: true
  attr :class, :string, default: ""
  slot :inner_block, required: true

  defp nav_link(assigns) do
    ~H"""
    <.link
      {if @navigate, do: [navigate: @navigate], else: [href: @href]}
      class={"#{@class} nav-link flex items-center px-3 py-2 gap-3 text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 rounded-md transition-colors"}
    >
      <.icon name={@icon} class="w-5 h-5 flex-shrink-0" />
      {render_slot(@inner_block)}
    </.link>
    """
  end

  @doc """
  Renders the mobile menu toggle button.
  """
  attr :class, :string, default: ""

  def mobile_menu_button(assigns) do
    ~H"""
    <button
      type="button"
      id="mobile-menu-button"
      class={"#{@class} lg:hidden inline-flex items-center justify-center p-2 rounded-md bg-zinc-900 hover:bg-zinc-700 text-white active:text-white/80 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"}
      phx-click={
        JS.remove_class("-translate-x-full", to: "#sidebar")
        |> JS.show(to: "#sidebar-backdrop")
        |> JS.hide(to: "#mobile-menu-button")
      }
    >
      <span class="sr-only">Open sidebar</span>
      <.icon name="hero-bars-3" class="w-6 h-6" />
    </button>
    """
  end
end
