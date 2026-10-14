/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy } from "@odoo/owl";
import { user } from "@web/core/user";

export class PharmacyDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.userName = user.name;

        const now = new Date();
        this.currentDateStr = now.toLocaleDateString('en-GB', { 
            weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' 
        });

        this.state = proxy({
            loading: true,
            data: {
                total_medicines: 0,
                in_stock: 0,
                low_stock: 0,
                out_of_stock: 0,
                total_batches: 0,
                valid_batches: 0,
                near_expiry_batches: 0,
                expired_batches: 0,
                total_prescriptions: 0,
                pending_prescriptions: 0,
                partially_dispensed: 0,
                fully_dispensed: 0,
                draft_prescriptions: 0,
                today_dispensed_count: 0,
                today_dispensed_amount: 0,
                total_dispensed_amount: 0,
                currency_symbol: '$',
                recent_dispenses: [],
                pending_prescriptions_list: [],
                low_stock_list: [],
                near_expiry_list: []
            }
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const result = await this.orm.call("dental.pharmacy.dashboard", "get_dashboard_data", []);
            if (result && typeof result === 'object') {
                Object.assign(this.state.data, result);
            }
        } catch (error) {
            console.error("Failed to load pharmacy dashboard analytics:", error);
            if (this.notification) {
                this.notification.add("Could not refresh pharmacy metrics.", { type: "warning" });
            }
        } finally {
            this.state.loading = false;
        }
    }

    openFilteredMedicines(filterType) {
        let domain = [["is_medicine", "=", true]];
        let title = "Dental Medicines";

        if (filterType === 'in_stock') {
            domain.push(["stock_status", "=", "in_stock"]);
            title = "In-Stock Medicines";
        } else if (filterType === 'low_stock') {
            domain.push(["stock_status", "=", "low_stock"]);
            title = "Low Stock Alerts";
        } else if (filterType === 'out_of_stock') {
            domain.push(["stock_status", "=", "out_of_stock"]);
            title = "Out-of-Stock Medicines";
        }

        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: 'product.template',
            domain: domain,
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            target: 'current'
        });
    }

    openFilteredBatches(filterType) {
        let domain = [["is_medicine", "=", true]];
        let title = "Medicine Batches";

        if (filterType === 'expired') {
            domain.push(["expiry_status", "=", "expired"]);
            title = "Expired Batches (Do Not Dispense)";
        } else if (filterType === 'near_expiry') {
            domain.push(["expiry_status", "=", "near_expiry"]);
            title = "Near Expiry Batches (≤ 60 Days)";
        } else if (filterType === 'valid') {
            domain.push(["expiry_status", "=", "valid"]);
            title = "Valid & Safe Batches";
        }

        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: 'stock.lot',
            domain: domain,
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    openFilteredPrescriptions(filterType) {
        let domain = [];
        let title = "Prescriptions";

        if (filterType === 'pending') {
            domain = [["state", "=", "confirmed"]];
            title = "Prescriptions Ready for Dispensing";
        } else if (filterType === 'partially_dispensed') {
            domain = [["state", "=", "partially_dispensed"]];
            title = "Partially Dispensed Prescriptions";
        } else if (filterType === 'fully_dispensed') {
            domain = [["state", "=", "fully_dispensed"]];
            title = "Fully Dispensed Prescriptions";
        } else if (filterType === 'all') {
            domain = [];
            title = "All Clinical Prescriptions";
        }

        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: 'dental.prescription',
            domain: domain,
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            target: 'current'
        });
    }

    openDispenseOrders(filterType) {
        let domain = [];
        let title = "Pharmacy Dispense Orders";

        if (filterType === 'today') {
            const now = new Date();
            const todayStr = now.toISOString().split('T')[0];
            domain = [
                ["dispense_date", ">=", todayStr + " 00:00:00"],
                ["dispense_date", "<=", todayStr + " 23:59:59"],
                ["state", "=", "dispensed"]
            ];
            title = "Today's Completed Dispenses";
        } else if (filterType === 'all') {
            domain = [];
            title = "All Dispensing Orders";
        }

        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: 'dental.pharmacy.dispense',
            domain: domain,
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    openRecord(model, id) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: model,
            res_id: id,
            views: [[false, 'form']],
            target: 'current'
        });
    }

    newPrescription() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Prescription',
            res_model: 'dental.prescription',
            views: [[false, 'form']],
            target: 'current'
        });
    }

    newDispense() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Dispense Order',
            res_model: 'dental.pharmacy.dispense',
            views: [[false, 'form']],
            target: 'current'
        });
    }

    newMedicine() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Add Medicine',
            res_model: 'product.template',
            views: [[false, 'form']],
            context: { default_is_medicine: true, default_tracking: 'lot' },
            target: 'current'
        });
    }

    formatCurrency(amount) {
        const symbol = this.state.data.currency_symbol || '$';
        const formatted = Number(amount || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        return `${symbol} ${formatted}`;
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        const dt = new Date(dateStr.replace(' ', 'T'));
        return dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
}

PharmacyDashboard.template = "dental_pharmacy.PharmacyDashboard";
registry.category("actions").add("dental_pharmacy.pharmacy_dashboard", PharmacyDashboard);
