import { Application } from "@hotwired/stimulus";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import FactNavigationController from "./fact_navigation_controller";
import GestureController from "./gesture_controller";

let application;
let card;
let area;
let older;
let newer;
let viewport;

function pointer(type, x, y = 100, options = {}, target = card) {
    const event = new Event(type, { bubbles: true });
    Object.assign(event, {
        pointerType: "touch",
        pointerId: 1,
        isPrimary: true,
        clientX: x,
        clientY: y,
        ...options,
    });
    target.dispatchEvent(event);
}

beforeEach(async () => {
    viewport = new EventTarget();
    viewport.scale = 1;
    vi.stubGlobal("visualViewport", viewport);
    document.body.innerHTML = `
        <div id="outside">Space outside the swipe area</div>
        <div class="fact-swipe-area" data-controller="gesture fact-navigation"
            data-action="pointerdown->gesture#start pointermove->gesture#move pointerup->gesture#finish pointercancel->gesture#cancel lostpointercapture->gesture#cancel blur@window->gesture#cancel gesture:swipe-left->fact-navigation#older gesture:swipe-right->fact-navigation#newer">
        <div id="padding">Padding outside the card</div>
        <article>
            <p>Fact content</p>
            <a href="/newer/" data-fact-navigation-target="newer">Newer</a>
            <a href="/older/" data-fact-navigation-target="older">Older</a>
        </article>
        </div>`;
    card = document.querySelector("article");
    area = document.querySelector(".fact-swipe-area");
    // jsdom has no native pointer capture; model its state and verify calls.
    const captured = new Set();
    area.setPointerCapture = vi.fn((id) => captured.add(id));
    area.hasPointerCapture = vi.fn((id) => captured.has(id));
    area.releasePointerCapture = vi.fn((id) => captured.delete(id));
    older = vi.fn();
    newer = vi.fn();
    for (const [name, handler] of [
        ["older", older],
        ["newer", newer],
    ]) {
        card.querySelector(
            `[data-fact-navigation-target="${name}"]`,
        ).addEventListener("click", (event) => {
            event.preventDefault();
            handler();
        });
    }
    application = Application.start();
    application.register("gesture", GestureController);
    application.register("fact-navigation", FactNavigationController);
    await new Promise((resolve) => setTimeout(resolve, 0));
});

afterEach(() => {
    application.stop();
    document.body.innerHTML = "";
    vi.unstubAllGlobals();
});

test.each([
    [200, 100, "older"],
    [100, 200, "newer"],
])("swiping from %i to %i opens the %s link", (start, end, direction) => {
    pointer("pointerdown", start);
    pointer("pointerup", end, 105, {}, area);
    expect(older).toHaveBeenCalledTimes(direction === "older" ? 1 : 0);
    expect(newer).toHaveBeenCalledTimes(direction === "newer" ? 1 : 0);
});

test.each([
    [200, 150, 100, "touch"], // Too short.
    [200, 100, 200, "touch"], // Diagonal.
    [200, 100, 100, "mouse"],
    [10, 150, 100, "touch"], // Browser back gesture.
    [window.innerWidth - 10, window.innerWidth - 150, 100, "touch"],
])(
    "ignores non-swipe gestures (%i, %i, %i, %s)",
    (start, end, y, pointerType) => {
        pointer("pointerdown", start, 100, { pointerType });
        pointer("pointerup", end, y, { pointerType });
        expect(older).not.toHaveBeenCalled();
        expect(newer).not.toHaveBeenCalled();
    },
);

test("does not turn vertical scrolling into navigation", () => {
    pointer("pointerdown", 200);
    pointer("pointermove", 195, 120);
    pointer("pointerup", 100, 125);
    expect(older).not.toHaveBeenCalled();
});

test.each(["pointercancel", "lostpointercapture", "blur", "multitouch"])(
    "cancels on %s",
    (reason) => {
        pointer("pointerdown", 200);
        if (reason === "multitouch") {
            pointer(
                "pointerdown",
                250,
                100,
                { pointerId: 2, isPrimary: false },
                area,
            );
        } else {
            (reason === "blur" ? window : area).dispatchEvent(
                new Event(reason),
            );
        }
        pointer("pointerup", 100);
        expect(older).not.toHaveBeenCalled();
    },
);

test("ignores swipes starting on a link", () => {
    pointer("pointerdown", 200, 100, {}, card.querySelector("a"));
    pointer("pointerup", 100);
    expect(older).not.toHaveBeenCalled();
});

test("does nothing when there is no adjacent fact", () => {
    card.querySelector('[data-fact-navigation-target="older"]').remove();
    pointer("pointerdown", 200);
    pointer("pointerup", 100);
    expect(older).not.toHaveBeenCalled();
    expect(newer).not.toHaveBeenCalled();
});

test.each([
    [200, 100, "swipe-left"],
    [100, 200, "swipe-right"],
])(
    "a swipe in the padding from %i to %i emits gesture:%s locally",
    (start, end, name) => {
        const listener = vi.fn();
        area.addEventListener(`gesture:${name}`, listener);
        try {
            pointer(
                "pointerdown",
                start,
                100,
                {},
                document.querySelector("#padding"),
            );
            pointer("pointerup", end, 100, {}, area);
            expect(listener).toHaveBeenCalledTimes(1);
            expect(listener.mock.calls[0][0].target).toBe(area);
            expect(older).toHaveBeenCalledTimes(name === "swipe-left" ? 1 : 0);
            expect(newer).toHaveBeenCalledTimes(name === "swipe-right" ? 1 : 0);
        } finally {
            area.removeEventListener(`gesture:${name}`, listener);
        }
    },
);

test("fact navigation responds to a local event independently of gesture detection", () => {
    area.dispatchEvent(new CustomEvent("gesture:swipe-left"));
    expect(older).toHaveBeenCalledTimes(1);
    expect(newer).not.toHaveBeenCalled();
});

test("swipes starting outside the area do not navigate even when ending inside", () => {
    pointer("pointerdown", 200, 100, {}, document.querySelector("#outside"));
    pointer("pointerup", 100);
    expect(older).not.toHaveBeenCalled();
    expect(newer).not.toHaveBeenCalled();
    expect(area.setPointerCapture).not.toHaveBeenCalled();
});

test("global and sibling gesture events do not navigate", () => {
    window.dispatchEvent(new CustomEvent("gesture:swipe-left"));
    document
        .querySelector("#outside")
        .dispatchEvent(
            new CustomEvent("gesture:swipe-right", { bubbles: true }),
        );
    expect(older).not.toHaveBeenCalled();
    expect(newer).not.toHaveBeenCalled();
});

test("captures an accepted pointer and releases it after navigating", () => {
    pointer("pointerdown", 200);
    expect(area.setPointerCapture).toHaveBeenCalledWith(1);
    // Captured events are delivered to the area even with outside coordinates.
    pointer("pointerup", -20, 100, {}, area);
    expect(older).toHaveBeenCalledTimes(1);
    expect(area.releasePointerCapture).toHaveBeenCalledWith(1);
});

test("releases capture when vertical scrolling cancels the gesture", () => {
    pointer("pointerdown", 200);
    pointer("pointermove", 195, 130, {}, area);
    expect(area.releasePointerCapture).toHaveBeenCalledWith(1);
    pointer("pointerup", 100);
    expect(older).not.toHaveBeenCalled();
});

test("disables swipes when zoomed and restores them after zooming out", () => {
    expect(area.hasAttribute("data-swipe-enabled")).toBe(true);
    viewport.scale = 2;
    viewport.dispatchEvent(new Event("resize"));
    expect(area.hasAttribute("data-swipe-enabled")).toBe(false);
    pointer("pointerdown", 200);
    pointer("pointerup", 100);
    expect(older).not.toHaveBeenCalled();
    expect(area.setPointerCapture).not.toHaveBeenCalled();

    viewport.scale = 1;
    viewport.dispatchEvent(new Event("resize"));
    expect(area.hasAttribute("data-swipe-enabled")).toBe(true);
    pointer("pointerdown", 200);
    pointer("pointerup", 100);
    expect(older).toHaveBeenCalledTimes(1);
});

test("zooming cancels a pending swipe and releases capture", () => {
    pointer("pointerdown", 200);
    viewport.scale = 2;
    viewport.dispatchEvent(new Event("resize"));
    expect(area.releasePointerCapture).toHaveBeenCalledWith(1);
    pointer("pointerup", 100);
    expect(older).not.toHaveBeenCalled();
});

test("checks zoom at pointerup before the viewport resize event arrives", () => {
    pointer("pointerdown", 200);
    viewport.scale = 2;
    pointer("pointerup", 100);
    expect(older).not.toHaveBeenCalled();
});

test("disconnect removes the viewport listener and restores native touch handling", async () => {
    const removeListener = vi.spyOn(viewport, "removeEventListener");
    pointer("pointerdown", 200);
    area.remove();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(removeListener).toHaveBeenCalledWith("resize", expect.any(Function));
    expect(area.hasAttribute("data-swipe-enabled")).toBe(false);
    expect(area.releasePointerCapture).toHaveBeenCalledWith(1);
});
