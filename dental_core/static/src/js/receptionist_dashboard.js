/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy } from "@odoo/owl";
import { user } from "@web/core/user";

export class ReceptionistDashboard extends Component {
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
                checked_in_patients: 0,
                new_patients_today: 0,
                upcoming_follow_ups: 0
            },
            today_appointments_list: [],
            waiting_queue: [],
            follow_ups: []
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
            // 1. Appointments
            const appointments = await this.orm.searchRead(
                "dental.appointment",
                [
                    ["date_start", ">=", utcStartStr],
                    ["date_start", "<=", utcEndStr]
                ],
                ["patient_id", "doctor_id", "date_start", "state", "treatment_id", "waiting_time", "token_number", "queue_priority"],
                { order: "date_start ASC" }
            );

            this.state.stats.today_appointments = appointments.length;
            this.state.today_appointments_list = appointments;
            
            // 2. Waiting Queue & Checked-in
            this.state.waiting_queue = appointments.filter(a => ['checked_in', 'in_consultation'].includes(a.state)).sort((a, b) => b.queue_priority - a.queue_priority);
            this.state.stats.waiting_patients = this.state.waiting_queue.length;
            this.state.stats.checked_in_patients = appointments.filter(a => a.state === 'checked_in').length;
            
            for (let wait of this.state.waiting_queue) {
                wait.formatted_waiting_time = Math.round(wait.waiting_time || 0);
            }

            // 3. New Patients
            const newPatients = await this.orm.searchCount("res.partner", [
                ["is_dental_patient", "=", true],
                ["create_date", ">=", utcStartStr],
                ["create_date", "<=", utcEndStr]
            ]);
            this.state.stats.new_patients_today = newPatients;

            // 4. Follow-ups
            const followUps = await this.orm.searchRead(
                "dental.appointment",
                [
                    ["state", "=", "completed"],
                    ["date_end", ">=", utcStartStr] // Placeholder logic for follow-ups, ideally based on follow-up flags
                ],
                ["patient_id", "doctor_id", "date_start", "treatment_id"],
                { order: "date_start DESC", limit: 5 }
            );
            this.state.follow_ups = followUps;
            this.state.stats.upcoming_follow_ups = await this.orm.searchCount("dental.appointment", [
                ["state", "in", ["pending", "confirmed"]],
                ["date_start", ">", utcEndStr] // All upcoming 
            ]);

        } catch (e) {
            console.error("Dashboard data load failed:", e);
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

    checkInPatient(id) {
        this.orm.call("dental.appointment", "action_check_in", [[id]]).then(() => {
            this.loadData();
        });
    }

    updateAppointmentState(id, methodName) {
        this.orm.call("dental.appointment", methodName, [[id]]).then(() => {
            this.loadData();
        });
    }
    
    openNewPatient() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            views: [[false, 'form']],
            target: 'current',
            context: { default_is_dental_patient: true }
        });
    }

    formatTime(datetimeStr) {
        if (!datetimeStr) return "";
        const dt = new Date(datetimeStr + "Z");
        return dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    
    formatDate(datetimeStr) {
        if (!datetimeStr) return "";
        const dt = new Date(datetimeStr + "Z");
        return dt.toLocaleDateString('en-GB');
    }
}

ReceptionistDashboard.template = "dental_core.ReceptionistDashboard";
registry.category("actions").add("dental_core.receptionist_dashboard", ReceptionistDashboard);
