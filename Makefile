# Makefile for Helm chart management in OmniPDF

# Default namespace and configurable chart
NAMESPACE ?= omnipdf
CHART_NAME ?= example-service           # Override via CLI, e.g., make install CHART_NAME=embedder-service
CHART_DIR ?= helm/$(CHART_NAME)
VALUES_FILE ?= $(CHART_DIR)/values.yaml

# Default port for port-forwarding (override as needed)
LOCAL_PORT ?= 8080
REMOTE_PORT ?= 8080

.PHONY: help install install-all upgrade uninstall lint status port-forward

help:
	@echo "Makefile commands for Helm chart management:"
	@echo ""
	@echo "Single-service commands:"
	@echo "  make install                Install chart (CHART_NAME)"
	@echo "  make upgrade                Upgrade chart (CHART_NAME)"
	@echo "  make uninstall              Uninstall chart (CHART_NAME)"
	@echo "  make lint                   Run helm lint on chart (CHART_NAME)"
	@echo "  make status                 Show status of Helm release (CHART_NAME)"
	@echo "  make port-forward           Port-forward service pod (default 8080:8080)"
	@echo ""
	@echo "Multi-service commands:"
	@echo "  make install-all            Install all charts under ./helm/"
	@echo "  make upgrade-all            Upgrade all charts under ./helm/"
	@echo "  make uninstall-all          Uninstall all charts under ./helm/"
	@echo ""
	@echo "Variables you can override:"
	@echo "  CHART_NAME=<service-name>   e.g. make install CHART_NAME=embedder-service"
	@echo "  LOCAL_PORT=<port>           e.g. make port-forward LOCAL_PORT=3000"
	@echo "  REMOTE_PORT=<port>          e.g. make port-forward REMOTE_PORT=5000"
	@echo ""
	@echo "IMPORTANT:"
	@echo "  Avoid underscores (_) in CHART_NAME or release names."
	@echo "  Use hyphens (-) instead to follow Kubernetes naming conventions (RFC 1123)."
	@echo "  Example: use chat-service ✅, not chat_service ❌"

install:
	helm install $(CHART_NAME) $(CHART_DIR) \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--values $(VALUES_FILE)

upgrade:
	helm upgrade $(CHART_NAME) $(CHART_DIR) \
		--namespace $(NAMESPACE) \
		--values $(VALUES_FILE)

uninstall:
	helm uninstall $(CHART_NAME) \
		--namespace $(NAMESPACE)

lint:
	helm lint $(CHART_DIR)

status:
	@echo "=== Helm Release Status ==="
	helm status $(CHART_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "=== Pod Status ==="
	kubectl get pods -n $(NAMESPACE) -l "app.kubernetes.io/name=$(CHART_NAME),app.kubernetes.io/instance=$(CHART_NAME)"

install-all:
	@echo "Installing all Helm charts under ./helm/..."
	@for dir in helm/*/; do \
		CHART=$$(basename $$dir); \
		echo "Installing chart: $$CHART"; \
		helm install $$CHART helm/$$CHART \
			--namespace $(NAMESPACE) \
			--create-namespace \
			--values helm/$$CHART/values.yaml || true; \
	done

upgrade-all:
	@echo "Upgrading all Helm charts under ./helm/..."
	@for dir in helm/*/; do \
		CHART=$$(basename $$dir); \
		echo "Upgrading chart: $$CHART"; \
		helm upgrade $$CHART helm/$$CHART \
			--namespace $(NAMESPACE) \
			--values helm/$$CHART/values.yaml || true; \
	done

uninstall-all:
	@echo "Uninstalling all Helm charts under ./helm/..."
	@for dir in helm/*/; do \
		CHART=$$(basename $$dir); \
		echo "Uninstalling chart: $$CHART"; \
		helm uninstall $$CHART \
			--namespace $(NAMESPACE) || true; \
	done

port-forward:
	kubectl --namespace $(NAMESPACE) port-forward \
	  $$(kubectl get pod -n $(NAMESPACE) -l "app.kubernetes.io/name=$(CHART_NAME),app.kubernetes.io/instance=$(CHART_NAME)" -o jsonpath="{.items[0].metadata.name}") \
	  $(LOCAL_PORT):$(REMOTE_PORT)
