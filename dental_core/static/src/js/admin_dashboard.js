/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy } from "@odoo/owl";
import { user } from "@web/core/user";

export class AdminDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.userName = user.name;
        
        const now = new Date();
        this.currentDateStr = now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
        
        this.state = proxy({
            stats: {
                today_appointments: 0,
                waiting_patients: 0,
                total_patients: 0,
                new_patients_today: 0,
                active_cases: 0,
                active_treatments: 0,
                total_staff: 0,
                pending_prescriptions: 0
            },
            today_appointments_list: [],
            recent_cases: [],
            staff_list: []
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        const formatUTC = (d) => {
            return d.getUTCFullYear() + '-' + 
                   String(d.getUTCMonth() + 1).padStart(2, '0') + '-' + 
                   String(d.getUTCDate()).padStart(2, '0') + ' ' + 
                   String(d.getUTCHours()).padStart(2, '0') + ':' + 
                   String(d.getUTCMinutes()).padStart(2, '0') + ':' + 
                   String(d.getUTCSeconds()).padStart(2, '0');
        };
        const now = new Date();
        const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
        const endOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
        const utcStartStr = formatUTC(startOfDay);
        const utcEndStr = formatUTC(endOfDay);
        
        try {
            // 1. Appointments Today
            const appointments = await this.orm.searchRead(
                "dental.appointment",
                [
                    ["date_start", ">=", utcStartStr],
                    ["date_start", "<=", utcEndStr]
                ],
                ["patient_id", "doctor_id", "date_start", "state", "treatment_id", "waiting_time"],
                { order: "date_start ASC", limit: 10 }
            );
            this.state.stats.today_appointments = appointments.length;
            this.state.today_appointments_list = appointments;

            // 2. Waiting Patients
            const waitingCount = await this.orm.searchCount("dental.appointment", [
                ["state", "in", ["checked_in", "in_consultation"]]
            ]);
            this.state.stats.waiting_patients = waitingCount;

            // 3. Patients (Total & New Today)
            this.state.stats.total_patients = await this.orm.searchCount("res.partner", [
                ["is_dental_patient", "=", true]
            ]);
            this.state.stats.new_patients_today = await this.orm.searchCount("res.partner", [
                ["is_dental_patient", "=", true],
                ["create_date", ">=", utcStartStr],
                ["create_date", "<=", utcEndStr]
            ]);

            // 4. Clinical Cases
            this.state.stats.active_cases = await this.orm.searchCount("dental.case", [
                ["state", "in", ["open", "under_treatment"]]
            ]);

            const cases = await this.orm.searchRead(
                "dental.case",
                [["state", "in", ["open", "under_treatment"]]],
                ["name", "patient_id", "doctor_id", "state", "chief_complaint"],
                { order: "create_date DESC", limit: 6 }
            );
            this.state.recent_cases = cases;

            // 5. Treatment Plans Ongoing
            this.state.stats.active_treatments = await this.orm.searchCount("dental.treatment.plan", [
                ["state", "in", ["draft", "confirmed", "in_progress"]]
            ]);

            // 6. Staff / Doctors
            this.state.stats.total_staff = await this.orm.searchCount("hr.employee", [
                ["dental_role", "!=", false]
            ]);
            this.state.staff_list = await this.orm.searchRead(
                "hr.employee",
                [["dental_role", "!=", false]],
                ["name", "dental_role", "work_email", "work_phone"],
                { limit: 5 }
            );

            // 7. Prescriptions Pending (if module exists)
            try {
                this.state.stats.pending_prescriptions = await this.orm.searchCount("dental.prescription", [
                    ["state", "in", ["draft", "confirmed", "partial"]]
                ]);
            } catch (ignore) {
                this.state.stats.pending_prescriptions = 0;
            }

        } catch (e) {
            console.error("Admin dashboard data load failed:", e);
        }
    }

    openAction(actionName) {
        this.action.doAction(actionName);
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

    formatTime(datetimeStr) {
        if (!datetimeStr) return "";
        const dt = new Date(datetimeStr + "Z");
        return dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
}

AdminDashboard.template = "dental_core.AdminDashboard";
registry.category("actions").add("dental_core.admin_dashboard", AdminDashboard);
