import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

DEMO_OTP = "123456"

def goto_local(page, filename="medstore.html"):
    url = Path(filename).resolve().as_uri()
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")

def sign_in(page, phone_number="9999999999"):
    # Click Sign In
    page.click("#signinBtn")
    page.wait_for_timeout(1000)

    # Fill phone
    page.fill("#phoneInput", phone_number)
    page.wait_for_timeout(1000)

    # Send OTP
    page.click("#sendOtp")
    page.wait_for_timeout(1000)

    # Enter OTP
    page.fill("#otpInput", DEMO_OTP)
    page.wait_for_timeout(1000)

    # Verify
    page.click("#verifyOtp")
    page.wait_for_timeout(1000)

    # Assert signed-in state
    expect(page.locator("#signinBtn .muted")).to_have_text("Signed In")

def add_medicine_to_cart(page, med_query: str):
    # Use the same search input class you used earlier
    search = page.locator(".d-header-search-input.search-color")
    search.fill(med_query)
    page.wait_for_timeout(1000)

    # Wait for grid to re-render
    grid = page.locator("#grid .card")
    expect(grid.first).to_be_visible()

    # Click Add to Cart on the first matching card
    cards = page.locator("#grid .card")
    count = cards.count()
    found = False
    for i in range(count):
        name = cards.nth(i).get_attribute("data-name") or ""
        if med_query.lower() in name.lower():
            cards.nth(i).locator("button.add-to-cart").click()
            page.wait_for_timeout(1000)
            found = True
            break

    if not found:
        raise RuntimeError(f"Medicine not found for query: {med_query}")


def open_cart_and_checkout(page, shipping=None):
    shipping = shipping or {
        "name": "Jane Doe",
        "phone": "9999999999",
        "line1": "221B Baker Street",
        "city": "Chennai",
        "zip": "600001",

        "payment": "cod",
    }

    # Open cart
    page.click("#cartBtn")
    page.wait_for_timeout(1000)
    expect(page.locator("#cartPanel")).to_have_class(re.compile(".*open.*"))

    # Proceed to checkout
    page.click("#proceedToCheckout")
    page.wait_for_timeout(1000)

    # Fill checkout form
    page.fill("#addressName", shipping["name"])
    page.fill("#addressPhone", shipping["phone"])
    page.fill("#addressLine1", shipping["line1"])
    page.fill("#city", shipping["city"])
    page.fill("#zip", shipping["zip"])
    page.select_option("#payment", shipping["payment"])
    page.wait_for_timeout(1000)

    # Place order
    page.click("#placeOrder")
    page.wait_for_timeout(1000)

    # Confirm success message appears
    expect(page.locator("#orderSuccess")).to_be_visible()

def order_medicine_playwright(medicine_name: str):
    with sync_playwright() as p:
        # Slow down each action by 1 second
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context()
        page = context.new_page()

        # Open your local HTML file
        goto_local(page, "medstore.html")
        sign_in(page, phone_number="9876543210")
        add_medicine_to_cart(page, medicine_name)
        open_cart_and_checkout(page)

        context.close()
        browser.close()

if __name__ == "__main__":
    # Simple CLI
    med = input("Enter medicine name: ").strip()
    if not med:
        med = "Dolo 650"
    order_medicine_playwright(med)
