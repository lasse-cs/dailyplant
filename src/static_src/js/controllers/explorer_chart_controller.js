import { Controller } from "@hotwired/stimulus";
import {
    forceCollide,
    forceLink,
    forceManyBody,
    forceSimulation,
    forceX,
    forceY,
    max,
    scaleRadial,
    select,
} from "d3";
import htmx from "htmx.org";

export default class extends Controller {
    static values = { data: String, width: Number, height: Number };
    static targets = [
        "chart",
        "detailsAnchor",
        "detailsClose",
        "detailsContent",
        "detailsPopover",
        "detailsTitle",
        "popover",
        "sizeLegend",
        "tooltipAnchor",
    ];

    connect() {
        this.loadData();
        this.scales();
        this.createChart();
        this.renderLegend();
        this.render();
    }

    loadData() {
        const chartData = JSON.parse(
            this.element.querySelector(`#${this.dataValue}`).textContent,
        );
        const nodeHash = chartData.nodes;
        this.typeNames = chartData.types;
        this.nodes = Object.values(nodeHash);
        this.edges = [];
        this.nodes.forEach((node) => {
            node.edges.forEach((edge) => {
                if (edge <= node.id) {
                    return;
                }
                this.edges.push({ source: node, target: nodeHash[edge] });
            });
        });
    }

    scales() {
        const maxDegree = max(this.nodes, (node) => node.degree);
        this.radialScale = scaleRadial().domain([0, maxDegree]).range([12, 36]);
    }

    createChart() {
        this.chart = select(this.chartTarget)
            .attr("viewBox", `0 0 ${this.widthValue} ${this.heightValue}`)
            .append("g")
            .attr(
                "transform",
                `translate(${this.widthValue / 2}, ${this.heightValue / 2})`,
            );
    }

    calculateLegendScaleFactor() {
        const chartMatrix = this.chartTarget.getScreenCTM();
        const legendMatrix = this.sizeLegendTarget.getScreenCTM();

        const chartPixelScale = Math.hypot(chartMatrix.a, chartMatrix.b);
        const legendPixelScale = Math.hypot(legendMatrix.a, legendMatrix.b);

        this.legendScaleFactor = chartPixelScale / legendPixelScale;
    }

    renderLegend() {
        this.calculateLegendScaleFactor();
        const legendRadius = (degree) =>
            this.radialScale(degree) * this.legendScaleFactor;

        const [minDegree, maxDegree] = this.radialScale.domain();
        const minSize = legendRadius(minDegree);
        const maxSize = legendRadius(maxDegree);
        select(this.sizeLegendTarget).attr(
            "aria-label",
            `Circle area represents connection counts from ${minDegree} to ${maxDegree}.`,
        );

        const sizes = select(this.sizeLegendTarget).append("g");
        this.sizeLegend = sizes;
        sizes.append("circle").attr("class", "node legend-node max-node");
        sizes.append("circle").attr("class", "node legend-node min-node");

        sizes.append("line").attr("class", "edge legend-edge max-edge");

        sizes.append("line").attr("class", "edge legend-edge min-edge");

        sizes
            .append("text")
            .attr("y", 0)
            .text(`${maxDegree}`)
            .attr("class", "legend-label max-label");

        sizes
            .append("text")
            .text(`${minDegree}`)
            .attr("class", "legend-label min-label");

        this.updateLegend(minSize, maxSize);
    }

    updateLegend(minSize, maxSize) {
        select(this.sizeLegendTarget)
            .select(".max-node")
            .attr("cx", maxSize)
            .attr("cy", maxSize)
            .attr("r", maxSize);

        select(this.sizeLegendTarget)
            .select(".min-node")
            .attr("cx", maxSize)
            .attr("cy", 2 * maxSize - minSize)
            .attr("r", minSize);

        select(this.sizeLegendTarget)
            .select(".max-edge")
            .attr("x1", maxSize)
            .attr("x2", 2.5 * maxSize);

        select(this.sizeLegendTarget)
            .select(".min-edge")
            .attr("x1", maxSize)
            .attr("y1", 2 * maxSize - 2 * minSize)
            .attr("x2", maxSize * 2.5)
            .attr("y2", 2 * maxSize - 2 * minSize);

        select(this.sizeLegendTarget)
            .select(".max-label")
            .attr("x", 2.5 * maxSize + 10);

        select(this.sizeLegendTarget)
            .select(".min-label")
            .attr("x", maxSize * 2.5 + 10)
            .attr("y", 2 * maxSize - 2 * minSize);

        this.resizeLegend();
    }

    resizeLegend() {
        const bounds = this.sizeLegend.node().getBBox();
        const padding = 4;
        const width = Math.ceil(bounds.width + 2 * padding);
        const height = Math.ceil(bounds.height + 2 * padding);

        select(this.sizeLegendTarget)
            .attr(
                "viewBox",
                `${bounds.x - padding} ${bounds.y - padding} ${width} ${height}`,
            )
            .attr("width", width)
            .attr("height", height);
    }

    render() {
        this.chart
            .selectAll(".edge")
            .data(this.edges)
            .join("line")
            .attr("class", "edge");

        this.chart
            .selectAll(".node")
            .data(this.nodes)
            .join("circle")
            .attr("class", (node) => `node ${node.type}`)
            .attr("r", (node) => {
                node.radius = this.radialScale(node.degree);
                return node.radius;
            })
            .attr(
                "data-action",
                `mouseenter->explorer-chart#showTooltip
                 mouseleave->explorer-chart#hideTooltip
                 focus->explorer-chart#showTooltip
                 blur->explorer-chart#hideTooltip
                 focus->explorer-chart#activateNode
                 click->explorer-chart#activateNode
                 click->explorer-chart#toggleDetails`,
            )
            .attr("tabindex", (_, index) => (index === 0 ? 0 : -1))
            .attr("role", "button")
            .attr("aria-controls", "explorer-details-popover")
            .attr("aria-expanded", "false")
            .attr("aria-label", (node) => {
                const connections = `${node.degree} connection${node.degree === 1 ? "" : "s"}`;
                return [node.title, this.typeNames[node.type], connections]
                    .filter(Boolean)
                    .join(", ");
            });

        const simulation = forceSimulation()
            .force("charge", forceManyBody().strength(-20).distanceMax(200))
            .force(
                "collide",
                forceCollide().radius((d) => d.radius + 20),
            )
            .force("x", forceX(0))
            .force("y", forceY(0))
            .force(
                "link",
                forceLink().id((d) => d.id),
            )
            .nodes(this.nodes)
            .on("tick", () => this.update());

        simulation.force("link").links(this.edges);
    }

    activateNode({ currentTarget }) {
        this.chart.selectAll(".node").attr("tabindex", -1);
        currentTarget.setAttribute("tabindex", "0");
    }

    handleKeydown(event) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            this.toggleDetails(event);
            return;
        }

        this.navigate(event);
    }

    navigate(event) {
        const directions = {
            ArrowDown: [0, 1],
            ArrowLeft: [-1, 0],
            ArrowRight: [1, 0],
            ArrowUp: [0, -1],
        };
        const direction = directions[event.key];
        const currentNode = event.target.__data__;
        if (!direction || !currentNode) {
            return;
        }

        event.preventDefault();
        let closestAlignedNode = null;
        let closestAlignedDistance = Number.POSITIVE_INFINITY;
        let closestDirectionalNode = null;
        let closestDirectionalDistance = Number.POSITIVE_INFINITY;

        for (const node of this.nodes) {
            if (node === currentNode) {
                continue;
            }

            const deltaX = node.x - currentNode.x;
            const deltaY = node.y - currentNode.y;
            const directionalDistance =
                deltaX * direction[0] + deltaY * direction[1];
            if (directionalDistance <= 0) {
                continue;
            }

            const distance = deltaX ** 2 + deltaY ** 2;
            if (distance < closestDirectionalDistance) {
                closestDirectionalNode = node;
                closestDirectionalDistance = distance;
            }

            const perpendicularDistance = Math.abs(
                deltaX * direction[1] - deltaY * direction[0],
            );
            const isAligned = perpendicularDistance <= directionalDistance;
            if (isAligned && distance < closestAlignedDistance) {
                closestAlignedNode = node;
                closestAlignedDistance = distance;
            }
        }

        const closestNode = closestAlignedNode ?? closestDirectionalNode;
        if (closestNode) {
            this.chart
                .selectAll(".node")
                .filter((node) => node === closestNode)
                .node()
                .focus();
        }
    }

    handleResize() {
        this.calculateLegendScaleFactor();
        const legendRadius = (degree) =>
            this.radialScale(degree) * this.legendScaleFactor;

        const [minDegree, maxDegree] = this.radialScale.domain();
        const minSize = legendRadius(minDegree);
        const maxSize = legendRadius(maxDegree);
        this.updateLegend(minSize, maxSize);
        this.updatePopoverAnchors();
    }

    handleScroll() {
        this.updatePopoverAnchors();
    }

    updatePopoverAnchors() {
        if (
            this.tooltipTrigger &&
            this.popoverTarget.matches(":popover-open")
        ) {
            this.positionAnchor(this.tooltipTrigger, this.tooltipAnchorTarget);
        }

        if (
            this.detailsTrigger &&
            this.detailsPopoverTarget.matches(":popover-open")
        ) {
            this.positionAnchor(this.detailsTrigger, this.detailsAnchorTarget);
        }
    }

    toggleDetails({ target }) {
        const node = target.__data__;
        if (!node) {
            return;
        }

        const isOpen = this.detailsPopoverTarget.matches(":popover-open");
        if (isOpen && this.detailsNode === node) {
            target.setAttribute("aria-expanded", "false");
            this.detailsNode = null;
            this.detailsPopoverTarget.hidePopover();
            return;
        }

        this.chart.selectAll(".node").attr("aria-expanded", "false");
        this.positionAnchor(target, this.detailsAnchorTarget);
        this.detailsTitleTarget.textContent = node.title;
        this.detailsContentTarget.textContent = "Loading details...";
        this.detailsContentTarget.setAttribute("aria-busy", "true");
        this.detailsPopoverTarget.dataset.nodeId = node.id;
        this.detailsNode = node;
        this.detailsTrigger = target;
        target.setAttribute("aria-expanded", "true");

        if (!isOpen) {
            this.detailsPopoverTarget.showPopover();
        }
        this.detailsCloseTarget.focus({ preventScroll: true });
        htmx.ajax("get", node.url, {
            source: this.detailsContentTarget,
            target: this.detailsContentTarget,
            swap: "innerHTML",
        });
    }

    finishDetailsRequest(event) {
        const node = this.detailsNode;
        if (!node || event.detail.requestConfig.path !== node.url) {
            return;
        }

        this.detailsContentTarget.setAttribute("aria-busy", "false");
        if (event.detail.successful) {
            return;
        }

        const message = document.createElement("p");
        message.textContent = "Details could not be loaded.";
        const link = document.createElement("a");
        link.href = node.url;
        link.textContent = "Open the full page";
        this.detailsContentTarget.replaceChildren(message, link);
    }

    closeDetails() {
        this.detailsFocusReturnTarget = this.detailsTrigger;
        this.detailsPopoverTarget.hidePopover();
    }

    prepareDetailsClose(event) {
        if (
            event.newState === "closed" &&
            this.detailsPopoverTarget.contains(document.activeElement)
        ) {
            this.suppressedTooltipTarget = this.detailsTrigger;
        }
    }

    syncDetailsState(event) {
        if (event.newState === "closed") {
            const focusReturnTarget = this.detailsFocusReturnTarget;
            this.chart.selectAll(".node").attr("aria-expanded", "false");
            this.detailsNode = null;
            this.detailsTrigger = null;
            this.detailsFocusReturnTarget = null;

            requestAnimationFrame(() => {
                if (focusReturnTarget?.isConnected) {
                    focusReturnTarget.focus({ preventScroll: true });
                }
            });
        }
    }

    positionAnchor(target, anchor) {
        const rect = target.getBoundingClientRect();
        anchor.style.left = `${rect.left}px`;
        anchor.style.top = `${rect.top}px`;
        anchor.style.width = `${rect.width}px`;
        anchor.style.height = `${rect.height}px`;
    }

    showTooltip({ target }) {
        if (target === this.suppressedTooltipTarget) {
            this.suppressedTooltipTarget = null;
            return;
        }

        this.tooltipTrigger = target;
        this.positionAnchor(target, this.tooltipAnchorTarget);
        this.popoverTarget.textContent = target.__data__.title;
        this.popoverTarget.showPopover();
    }

    hideTooltip() {
        this.popoverTarget.hidePopover();
        this.tooltipTrigger = null;
    }

    update() {
        select(this.chartTarget)
            .selectAll(".edge")
            .attr("x1", (d) => d.source.x)
            .attr("y1", (d) => d.source.y)
            .attr("x2", (d) => d.target.x)
            .attr("y2", (d) => d.target.y);

        select(this.chartTarget)
            .selectAll(".node")
            .attr("cx", (d) => d.x)
            .attr("cy", (d) => d.y);
    }
}
