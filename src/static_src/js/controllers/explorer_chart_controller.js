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

const SMALL_SCREEN_QUERY = "(max-width: 35rem)";
const LARGE_SCREEN_ASPECT_RATIO = 4 / 3;
const SMALL_SCREEN_ASPECT_RATIO = 5 / 6;
const NODE_RADIUS_RANGE = [12, 36];
const SMALL_SCREEN_NODE_RADIUS_RANGE = [18, 44];

export default class extends Controller {
    static values = { data: String, height: Number };
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

    initialize() {
        this.detailsCache = new Map();
    }

    connect() {
        this.loadData();
        this.createChart();
        this.updateResponsiveLayout();
        this.render();
        this.layout();
        this.renderLegend();
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
        const radiusRange = this.smallScreen
            ? SMALL_SCREEN_NODE_RADIUS_RANGE
            : NODE_RADIUS_RANGE;
        this.collisionScale = scaleRadial()
            .domain([0, maxDegree])
            .range(NODE_RADIUS_RANGE);
        this.radialScale = scaleRadial()
            .domain([0, maxDegree])
            .range(radiusRange);
    }

    createChart() {
        this.chart = select(this.chartTarget).append("g");
    }

    updateChartDimensions() {
        select(this.chartTarget).attr(
            "viewBox",
            `0 0 ${this.width} ${this.heightValue}`,
        );
        this.chart.attr(
            "transform",
            `translate(${this.width / 2}, ${this.heightValue / 2})`,
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
        select(this.sizeLegendTarget)
            .select("desc")
            .text(
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
            .each((node) => {
                node.collisionRadius = this.collisionScale(node.degree);
            })
            .attr("class", (node) => `node ${node.type}`)
            .attr("r", (node) => this.radialScale(node.degree))
            .attr("cx", 2 * this.width)
            .attr("cy", 2 * this.heightValue)
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
    }

    layout() {
        const simulation = forceSimulation()
            .force("charge", forceManyBody().strength(-20).distanceMax(200))
            .force(
                "collide",
                forceCollide().radius((d) => d.collisionRadius + 20),
            )
            .force("x", forceX(0))
            .force("y", forceY(0))
            .force(
                "link",
                forceLink().id((d) => d.id),
            )
            .nodes(this.nodes)
            .stop();

        simulation.force("link").links(this.edges);

        // Run the simulation to its end, then draw.
        const iterations = Math.ceil(
            Math.log(simulation.alphaMin()) /
                Math.log(1 - simulation.alphaDecay()),
        );

        simulation.tick(iterations);
        this.update();
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
        const smallScreen = window.matchMedia(SMALL_SCREEN_QUERY).matches;
        if (smallScreen !== this.smallScreen) {
            this.updateResponsiveLayout(smallScreen);
        }

        this.calculateLegendScaleFactor();
        const legendRadius = (degree) =>
            this.radialScale(degree) * this.legendScaleFactor;

        const [minDegree, maxDegree] = this.radialScale.domain();
        const minSize = legendRadius(minDegree);
        const maxSize = legendRadius(maxDegree);
        this.updateLegend(minSize, maxSize);
        this.updatePopoverAnchors();
    }

    updateResponsiveLayout(
        smallScreen = window.matchMedia(SMALL_SCREEN_QUERY).matches,
    ) {
        this.setResponsiveWidth(smallScreen);
        this.scales();
        this.updateChartDimensions();
        this.chart
            .selectAll(".node")
            .attr("r", (node) => this.radialScale(node.degree));
    }

    setResponsiveWidth(smallScreen) {
        this.smallScreen = smallScreen;
        const aspectRatio = smallScreen
            ? SMALL_SCREEN_ASPECT_RATIO
            : LARGE_SCREEN_ASPECT_RATIO;
        this.width = this.heightValue * aspectRatio;
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
        this.detailsPopoverTarget.dataset.nodeId = node.id;
        this.detailsNode = node;
        this.detailsTrigger = target;
        target.setAttribute("aria-expanded", "true");

        if (!isOpen) {
            this.detailsPopoverTarget.showPopover();
        }
        this.detailsCloseTarget.focus({ preventScroll: true });

        const cachedDetails = this.detailsCache.get(node.url);
        if (cachedDetails !== undefined) {
            htmx.trigger(this.detailsContentTarget, "htmx:abort");
            this.detailsContentTarget.innerHTML = cachedDetails;
            this.detailsContentTarget.setAttribute("aria-busy", "false");
            return;
        }

        this.detailsContentTarget.textContent = "Loading details...";
        this.detailsContentTarget.setAttribute("aria-busy", "true");
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
            this.detailsCache.set(
                node.url,
                this.detailsContentTarget.innerHTML,
            );
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
