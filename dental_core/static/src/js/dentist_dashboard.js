/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy } from "@odoo/owl";
import { user } from "@web/core/user";

export class DentistDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.userName = user.name;
        
        const now = new Date();
        this.currentDateStr = now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
        
        this.state = proxy({
            stats: {
                today_appointments: 0,
                completed_appointments: 0,
                pending_appointments: 0,
                waiting_patients: 0,
                avg_waiting_time: 0,
                active_cases: 0,
                under_treatment_cases: 0,
                today_sessions: 0,
                completed_sessions: 0,
                pending_sessions: 0
            },
            today_appointments_list: [],
            recent_cases: [],
            today_sessions_list: [],
            waiting_queue: [],
            calendar_events: []
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        const uid = user.userId;
        const todayStr = new Date().toISOString().split('T')[0];
        
        try {
            // 1. Appointments
            const appointments = await this.orm.searchRead(
                "dental.appointment",
                [
                    ["doctor_id.user_id", "=", uid],
                    ["date_start", ">=", todayStr + " 00:00:00"],
                    ["date_start", "<=", todayStr + " 23:59:59"]
                ],
                ["patient_id", "date_start", "state", "treatment_id", "waiting_time"],
                { order: "date_start ASC" }
            );

            this.state.stats.today_appointments = appointments.length;
            this.state.stats.completed_appointments = appointments.filter(a => a.state === 'completed').length;
            this.state.stats.pending_appointments = appointments.filter(a => ['pending', 'confirmed', 'checked_in', 'in_consultation'].includes(a.state)).length;
            
            this.state.today_appointments_list = appointments;
            this.state.calendar_events = appointments;
            
            // 2. Waiting Queue
            this.state.waiting_queue = appointments.filter(a => ['checked_in', 'in_consultation'].includes(a.state));
            this.state.stats.waiting_patients = this.state.waiting_queue.length;
            
            if (this.state.waiting_queue.length > 0) {
                let totalWait = 0;
                for (let wait of this.state.waiting_queue) {
                    wait.formatted_waiting_time = Math.round(wait.waiting_time || 0);
                    totalWait += (wait.waiting_time || 0);
                }
                this.state.stats.avg_waiting_time = Math.round(totalWait / this.state.waiting_queue.length);
            }

            // 3. Cases
            const cases = await this.orm.searchRead(
                "dental.case",
                [
                    ["doctor_id.user_id", "=", uid],
                    ["state", "in", ["open", "under_treatment"]]
                ],
                ["name", "patient_id", "state", "chief_complaint"],
                { order: "create_date DESC", limit: 5 }
            );
            this.state.stats.active_cases = await this.orm.searchCount("dental.case", [
                ["doctor_id.user_id", "=", uid],
                ["state", "in", ["open", "under_treatment"]]
            ]);
            this.state.stats.under_treatment_cases = await this.orm.searchCount("dental.case", [
                ["doctor_id.user_id", "=", uid],
                ["state", "=", "under_treatment"]
            ]);
            this.state.recent_cases = cases;

            // 4. Treatment Sessions
            const sessions = await this.orm.searchRead(
                "dental.treatment.session",
                [
                    ["doctor_id.user_id", "=", uid],
                    ["session_date", ">=", todayStr + " 00:00:00"],
                    ["session_date", "<=", todayStr + " 23:59:59"]
                ],
                ["name", "patient_id", "state", "plan_line_id", "session_date"],
                { order: "session_date ASC", limit: 5 }
            );
            
            const allTodaySessions = await this.orm.searchRead(
                "dental.treatment.session",
                [
                    ["doctor_id.user_id", "=", uid],
                    ["session_date", ">=", todayStr + " 00:00:00"],
                    ["session_date", "<=", todayStr + " 23:59:59"]
                ],
                ["state"]
            );
            
            this.state.stats.today_sessions = allTodaySessions.length;
            this.state.stats.completed_sessions = allTodaySessions.filter(s => s.state === 'completed').length;
            this.state.stats.pending_sessions = allTodaySessions.filter(s => ['planned', 'in_progress'].includes(s.state)).length;
            this.state.today_sessions_list = sessions;

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

    startConsultation(id) {
        this.orm.call("dental.appointment", "action_start_consultation", [[id]]).then(() => {
            this.loadData();
        });
    }
    
    formatTime(datetimeStr) {
        if (!datetimeStr) return "";
        const dt = new Date(datetimeStr + "Z");
        return dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
}

DentistDashboard.template = "dental_core.DentistDashboard";
registry.category("actions").add("dental_core.dentist_dashboard", DentistDashboard);
