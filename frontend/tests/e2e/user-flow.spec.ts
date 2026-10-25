import { test, expect } from "@playwright/test";

test.describe("Full End-to-End User Planning Journey", () => {
  const eventId = "evt-e2e-123";

  test.beforeEach(async ({ page }) => {
    // Intercept backend API calls with deterministic contract-compliant responses
    await page.route("**/api/auth/register", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: {
            id: "user-e2e-1",
            email: "alex@eventwise.io",
            full_name: "Alex Morgan",
            is_active: true,
          },
          token: {
            access_token: "mock-jwt-token-xyz",
            token_type: "bearer",
          },
        }),
      });
    });

    await page.route("**/api/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "user-e2e-1",
          email: "alex@eventwise.io",
          full_name: "Alex Morgan",
          is_active: true,
        }),
      });
    });

    await page.route("**/api/events", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: eventId,
            user_id: "user-e2e-1",
            title: "Alex & Jordan Rustic Autumn Gala",
            description: "A warm celebration with 120 guests and autumn palette.",
            event_type: "wedding",
            status: "planning",
            start_date: "2026-10-15T16:00:00Z",
            end_date: "2026-10-15T23:00:00Z",
            location: "Timberline Barn & Garden, Napa, CA",
            total_budget: 35000,
            currency: "USD",
            estimated_guests: 120,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            events: [
              {
                id: eventId,
                user_id: "user-e2e-1",
                title: "Alex & Jordan Rustic Autumn Gala",
                description: "A warm celebration with 120 guests and autumn palette.",
                event_type: "wedding",
                status: "planning",
                start_date: "2026-10-15T16:00:00Z",
                end_date: "2026-10-15T23:00:00Z",
                location: "Timberline Barn & Garden, Napa, CA",
                total_budget: 35000,
                currency: "USD",
                estimated_guests: 120,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
            ],
            total: 1,
            page: 1,
            page_size: 20,
          }),
        });
      }
    });

    await page.route(`**/api/events/${eventId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          event: {
            id: eventId,
            user_id: "user-e2e-1",
            title: "Alex & Jordan Rustic Autumn Gala",
            description: "A warm celebration with 120 guests and autumn palette.",
            event_type: "wedding",
            status: "planning",
            start_date: "2026-10-15T16:00:00Z",
            end_date: "2026-10-15T23:00:00Z",
            location: "Timberline Barn & Garden, Napa, CA",
            total_budget: 35000,
            currency: "USD",
            estimated_guests: 120,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          budget_summary: {
            total_budget: 35000,
            total_spent: 12500,
            remaining_budget: 22500,
          },
          timeline_summary: {
            total_tasks: 8,
            completed_tasks: 3,
            upcoming_tasks: 5,
          },
          guest_summary: {
            total_guests: 120,
            confirmed_guests: 64,
            declined_guests: 8,
            pending_guests: 48,
          },
        }),
      });
    });

    await page.route(`**/api/events/${eventId}/concept`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          event_id: eventId,
          vibe_summary: "Rustic-Chic Bohemian Sunset with Pampas Grass & Firepits",
          color_palette: [
            { name: "Terracotta", hex: "#C86446", meaning: "Earthy warmth" },
            { name: "Pampas Tan", hex: "#D6C7A1", meaning: "Neutral grass" },
            { name: "Sage Olive", hex: "#8A9A86", meaning: "Botanical freshness" },
            { name: "Amber Festoon", hex: "#E8A34F", meaning: "Dusk glow" },
          ],
          decor_motifs: [
            "Floating pampas chandeliers",
            "Handmade terracotta pottery table numbers",
            "Woven rattan lounge vignettes",
          ],
          layout_ideas: [
            "Circular ceremony seating under harvest arbor",
            "U-shaped farm tables for communal dining",
            "Central sunken firepit cocktail area",
          ],
          high_level_schedule: [
            { phase: "Guest Arrival", time: "16:00", activity: "Welcome cider & acoustic duo" },
            { phase: "Ceremony", time: "17:00", activity: "Vows exchange at sunset" },
            { phase: "Dinner & Toasts", time: "18:30", activity: "Farm-to-table banquet" },
          ],
          generated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/events/${eventId}/budget`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          event_id: eventId,
          total_budget: 35000,
          total_spent: 12500,
          remaining_budget: 22500,
          items: [
            {
              id: "b-1",
              event_id: eventId,
              category: "Catering & Bar",
              name: "Artisanal farm-to-table buffet & cocktail service",
              estimated_cost: 14000,
              actual_cost: 14000,
              vendor_id: "v-1",
              notes: "120 guests tasting completed",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            {
              id: "b-2",
              event_id: eventId,
              category: "Venue",
              name: "Timberline Barn rental",
              estimated_cost: 8750,
              actual_cost: 0,
              vendor_id: "v-2",
              notes: "Deposit due next month",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        }),
      });
    });

    await page.route(`**/api/events/${eventId}/timeline`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          event_id: eventId,
          total_tasks: 4,
          completed_tasks: 2,
          tasks: [
            {
              id: "t-1",
              event_id: eventId,
              title: "Finalize catering agreement and menu selection",
              due_date: "2026-07-01T12:00:00Z",
              status: "completed",
              phase: "Planning",
              assigned_to: "Alex",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            {
              id: "t-2",
              event_id: eventId,
              title: "Send digital RSVP invitations to guests",
              due_date: "2026-08-01T12:00:00Z",
              status: "pending",
              phase: "Execution",
              assigned_to: "Jordan",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        }),
      });
    });

    await page.route(`**/api/events/${eventId}/chat`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          event_id: eventId,
          reply:
            "I have reviewed your $35,000 budget for 120 guests. Catering is safely locked at $14,000, leaving ample room for your floral staging.",
          tool_calls_executed: [
            {
              tool_name: "calculate_budget",
              arguments: { total_budget: 35000, guest_count: 120 },
              result_summary: "Confirmed allocation meets target percentages",
              status: "success",
            },
          ],
        }),
      });
    });

    await page.route(`**/api/public/events/${eventId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: eventId,
          title: "Alex & Jordan Rustic Autumn Gala",
          description: "You are warmly invited to join us for an evening of rustic dining and celebration.",
          event_type: "wedding",
          start_date: "2026-10-15T16:00:00Z",
          location: "Timberline Barn & Garden, Napa, CA",
        }),
      });
    });

    await page.route(`**/api/public/events/${eventId}/rsvp`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Thank you for confirming! Your party of 2 has been registered.",
          guest: {
            id: "guest-999",
            event_id: eventId,
            full_name: "Taylor Swift",
            email: "taylor@example.com",
            rsvp_status: "attending",
            plus_ones: 1,
            dietary_restrictions: ["Vegetarian"],
            notes: "Looking forward to celebrating with you both!",
            created_at: new Date().toISOString(),
          },
        }),
      });
    });
  });

  test("completes end-to-end journey: signup → create event → generate plan → view budget/timeline → chat → RSVP", async ({
    page,
  }) => {
    // 1. Signup Flow
    await page.goto("/signup");
    await expect(page.getByRole("heading", { name: /create an account/i })).toBeVisible();

    await page.fill("#full_name", "Alex Morgan");
    await page.fill("#email", "alex@eventwise.io");
    await page.fill("#password", "Password123!");
    await page.getByRole("button", { name: /create account/i }).click();

    // 2. Navigate to Events and Create Event
    await page.goto("/dashboard/events");
    await expect(page.getByRole("heading", { name: "Events" })).toBeVisible();

    // Open Event Form modal
    const createBtn = page.getByRole("button", { name: /\+ new event/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
    } else {
      await page.getByRole("button", { name: /\+ create your first event/i }).click();
    }

    // Modal is open
    await expect(page.getByRole("dialog", { name: /create new event/i })).toBeVisible();

    await page.fill("#event-title", "Alex & Jordan Rustic Autumn Gala");
    await page.fill("#event-description", "A warm celebration with 120 guests and autumn palette.");
    await page.selectOption("#event-type", "wedding");
    await page.fill("#event-budget", "35000");
    await page.fill("#event-guests", "120");
    await page.fill("#event-location", "Timberline Barn & Garden, Napa, CA");

    // Click submit in modal
    await page.getByRole("dialog", { name: /create new event/i })
      .getByRole("button", { name: /^create$/i })
      .click();

    // 3. Generate Concept / Plan
    await page.goto(`/dashboard/events/${eventId}/concept`);
    await expect(page.getByRole("heading", { name: /concept & visual moodboard/i })).toBeVisible();

    // Click an inspiration chip to populate vibe brief
    const chip = page.getByRole("button", { name: /\+ rustic-chic bohemian sunset/i });
    await chip.click();

    // Submit concept generation
    await page.getByRole("button", { name: /generate concept board/i }).click();

    // Verify concept board details rendered
    await expect(page.getByText("Terracotta")).toBeVisible();
    await expect(page.getByText("Floating pampas chandeliers")).toBeVisible();

    // 4. View Budget & Timeline
    await page.goto(`/dashboard/events/${eventId}/budget`);
    await expect(page.getByRole("region", { name: /budget breakdown/i })).toBeVisible();
    await expect(page.getByText("Artisanal farm-to-table buffet & cocktail service")).toBeVisible();

    await page.goto(`/dashboard/events/${eventId}/timeline`);
    await expect(page.getByRole("region", { name: /timeline tasks view/i })).toBeVisible();
    await expect(page.getByText("Finalize catering agreement and menu selection")).toBeVisible();

    // 5. Chat with AI Concierge
    await page.goto("/dashboard/ai-chat");
    await expect(page.getByRole("heading", { name: "AI Planning Concierge" })).toBeVisible();

    const chatInput = page.getByRole("textbox", { name: /message prompt to ai concierge/i });
    await chatInput.fill("How should I allocate a $35,000 budget for 120 guests?");
    await page.getByRole("button", { name: /send message/i }).click();

    // Verify assistant responds with tool usage
    await expect(
      page.getByText(/I have reviewed your \$35,000 budget for 120 guests/i),
    ).toBeVisible();
    await expect(page.getByText(/calculate_budget/i)).toBeVisible();

    // 6. Public Digital RSVP
    await page.goto(`/rsvp/${eventId}`);
    await expect(page.getByRole("heading", { name: /kindly respond/i })).toBeVisible();

    await page.fill("#guest-fullname", "Taylor Swift");
    await page.fill("#guest-email", "taylor@example.com");

    // Select attendance
    await page.getByRole("radio", { name: /joyfully accept/i }).click();

    // Select plus-ones
    await page.getByRole("button", { name: /select 1 plus-ones/i }).click();

    // Select dietary preference
    await page.getByRole("button", { name: /\+ vegetarian/i }).click();

    // Submit RSVP
    await page.getByRole("button", { name: /submit rsvp response/i }).click();

    // Verify success confirmation card
    await expect(page.getByRole("heading", { name: /rsvp successfully received/i })).toBeVisible();
    await expect(page.getByText("Thank you for confirming!")).toBeVisible();
    await expect(page.getByText("Taylor Swift")).toBeVisible();
  });
});
