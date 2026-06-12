import { Controller } from "@hotwired/stimulus";
import htmx from "htmx.org";

export default class extends Controller {
    static targets = ["template"];

    connect() {
        if (!this.hasTemplateTarget) {
            return;
        }
        const clone = document.importNode(this.templateTarget.content, true);
        this.element.textContent = "";
        this.element.appendChild(clone);
        htmx.process(this.element);
    }
}
