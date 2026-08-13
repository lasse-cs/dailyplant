import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    toggle() {
        const controlledElement = document.getElementById(
            this.element.getAttribute("aria-controls"),
        );
        controlledElement.hidden = !controlledElement.hidden;
        this.element.setAttribute(
            "aria-expanded",
            String(!controlledElement.hidden),
        );
    }
}
