import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["link"];

    connect() {
        this.sections = this.linkTargets.flatMap((link) => {
            const heading = document.getElementById(link.dataset.tocAnchor);
            return heading ? [{ heading, link }] : [];
        });

        if (!this.sections.length) return;

        this.updateCurrentSection();
    }

    updateCurrentSection() {
        const readingLine = Math.min(window.innerHeight * 0.2, 160);
        let currentSection = null;

        for (const section of this.sections) {
            if (section.heading.getBoundingClientRect().top > readingLine) break;
            currentSection = section;
        }

        if (currentSection === this.currentSection) return;

        this.currentSection?.link.removeAttribute("aria-current");
        currentSection?.link.setAttribute("aria-current", "location");
        this.currentSection = currentSection;
    }
}
