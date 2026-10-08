import { Controller } from "@hotwired/stimulus";

const NORMAL_VIEWPORT_SCALE = 1;
const ZOOM_SCALE_TOLERANCE = 0.01;
const BROWSER_GESTURE_EDGE_INSET_PX = 24;
const VERTICAL_SCROLL_THRESHOLD_PX = 10;
const MIN_SWIPE_DISTANCE_PX = 60;
const MIN_HORIZONTAL_TO_VERTICAL_RATIO = 2;
const MAX_SWIPE_DURATION_MS = 800;

const interactive =
    "a, button, input, textarea, select, summary, [contenteditable], [role='button'], [role='slider']";

export default class extends Controller {
    connect() {
        this.viewport = window.visualViewport;
        this.updateSwipeState = () => {
            this.element.toggleAttribute("data-swipe-enabled", !this.isZoomed);
            if (this.isZoomed) this.cancel();
        };
        this.viewport?.addEventListener("resize", this.updateSwipeState);
        this.updateSwipeState();
    }

    get isZoomed() {
        // Allow for rounding around the normal viewport scale.
        return (
            (this.viewport?.scale ?? NORMAL_VIEWPORT_SCALE) >
            NORMAL_VIEWPORT_SCALE + ZOOM_SCALE_TOLERANCE
        );
    }

    start(event) {
        this.cancel();
        if (
            this.isZoomed ||
            event.pointerType !== "touch" ||
            !event.isPrimary ||
            event.clientX < BROWSER_GESTURE_EDGE_INSET_PX ||
            event.clientX > window.innerWidth - BROWSER_GESTURE_EDGE_INSET_PX ||
            event.target.closest(interactive) ||
            window.getSelection()?.toString()
        ) {
            return;
        }

        this.gesture = {
            id: event.pointerId,
            x: event.clientX,
            y: event.clientY,
            time: event.timeStamp,
        };
        // Keep receiving this pointer's events even outside the swipe area.
        this.element.setPointerCapture(event.pointerId);
    }

    move(event) {
        if (!this.gesture || event.pointerId !== this.gesture.id) return;

        const dx = Math.abs(event.clientX - this.gesture.x);
        const dy = Math.abs(event.clientY - this.gesture.y);
        // Once a gesture becomes a vertical scroll, it cannot become a swipe.
        if (dy > VERTICAL_SCROLL_THRESHOLD_PX && dy >= dx) this.cancel();
    }

    finish(event) {
        const gesture = this.gesture;
        if (!gesture || event.pointerId !== gesture.id) return;
        this.cancel();

        const dx = event.clientX - gesture.x;
        const dy = event.clientY - gesture.y;
        if (
            this.isZoomed ||
            Math.abs(dx) < MIN_SWIPE_DISTANCE_PX ||
            Math.abs(dx) < Math.abs(dy) * MIN_HORIZONTAL_TO_VERTICAL_RATIO ||
            event.timeStamp - gesture.time > MAX_SWIPE_DURATION_MS ||
            window.getSelection()?.toString()
        ) {
            return;
        }

        this.dispatch(dx < 0 ? "swipe-left" : "swipe-right");
    }

    cancel() {
        const gesture = this.gesture;
        this.gesture = null;
        if (gesture && this.element.hasPointerCapture(gesture.id)) {
            this.element.releasePointerCapture(gesture.id);
        }
    }

    disconnect() {
        this.viewport?.removeEventListener("resize", this.updateSwipeState);
        this.element.removeAttribute("data-swipe-enabled");
        this.cancel();
    }
}
