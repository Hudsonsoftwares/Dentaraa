/** @odoo-module **/

import { Component, onMounted, onPatched, onWillUnmount, onWillUpdateProps, signal, useProps, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class DentalOdontogram3DField extends Component {
    static template = "dental_core.OdontogramField";
    props = useProps({
        ...standardFieldProps,
    });

    canvasContainerRef = signal.ref();
    viewportRef = signal.ref();

    get containerEl() {
        return typeof this.canvasContainerRef === "function" ? this.canvasContainerRef() : (this.canvasContainerRef?.el || null);
    }

    get viewportEl() {
        return typeof this.viewportRef === "function" ? this.viewportElInternal : (this.viewportRef?.el || null);
    }

    get viewportElInternal() {
        return typeof this.viewportRef === "function" ? this.viewportRef() : null;
    }

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.patientId = this.getPatientId();
        this.caseId = this.getCaseId();

        this.state = proxy({
            patientId: this.patientId,
            patientName: "",
            patientRef: "",
            patientAge: null,
            patientDob: "",
            caseId: this.caseId,
            caseName: "",
            canEdit: false,
            isDentist: false,
            selectedTooth: null,
            dentitionType: "permanent", // 'primary' (20), 'mixed' (mixed), 'permanent' (32)
            suggestedDentition: "permanent",
            currentView: "front",
            hoveredTooth: null,
            hoveredToothInfo: "",
            tooltipX: 0,
            tooltipY: 0,
            activePanelTab: "record",
            isSaving: false,
            isLoadingModel: false,
            stats: {
                sound: 32,
                caries: 0,
                restoration: 0,
                crown: 0,
                root_canal: 0,
                missing: 0,
                total_teeth: 32,
            },
            diagnosisMasters: [],
            newFinding: {
                condition: "caries",
                diagnosis_id: "",
                surfaces: ["O"],
                severity: "moderate",
                treatment_indicated: "",
                notes: "",
            },
            teeth: {},
        });

        // 3D Scene Properties
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.toothMeshes = {}; // toothNumber -> { mesh, group, isUpper, basePos, toothNumber }
        this.raycaster = null;
        this.pointer = null;
        this.animationFrameId = null;
        this.resizeObserver = null;
        this.intersectionObserver = null;
        this.tabMutationObserver = null;
        this.onWindowResizeBound = null;
        this.is3DReady = false;

        onMounted(async () => {
            await this.init3DScene();
            await this.loadOdontogram();
        });

        onWillUpdateProps(async (nextProps) => {
            const nextPatientId = this.getPatientId(nextProps);
            const nextCaseId = this.getCaseId(nextProps);
            if (nextPatientId !== this.patientId || nextCaseId !== this.caseId) {
                this.patientId = nextPatientId;
                this.caseId = nextCaseId;
                await this.loadOdontogram();
            }
        });

        onPatched(async () => {
            if (!this.is3DReady) {
                await this.init3DScene();
            }
            const currentPatientId = this.getPatientId();
            const currentCaseId = this.getCaseId();
            if (currentPatientId !== this.patientId || currentCaseId !== this.caseId) {
                this.patientId = currentPatientId;
                this.caseId = currentCaseId;
                await this.loadOdontogram();
            }
        });

        onWillUnmount(() => {
            this.cleanup3D();
        });
    }

    getPatientId(props = this.props) {
        const p = props?.record?.data?.patient_id;
        if (!p) return false;
        if (typeof p === "object" && p.id) return p.id;
        if (Array.isArray(p) && p.length > 0) return p[0];
        if (typeof p === "number") return p;
        return false;
    }

    getCaseId(props = this.props) {
        return props?.record?.resId || props?.record?.data?.id || false;
    }

    // -------------------------------------------------------------------------
    // Getters for Template
    // -------------------------------------------------------------------------

    get upperRightTeeth() {
        if (this.state.dentitionType === "primary") {
            return ["55", "54", "53", "52", "51"];
        } else if (this.state.dentitionType === "mixed") {
            return ["16", "55", "54", "53", "12", "11"];
        }
        return ["18", "17", "16", "15", "14", "13", "12", "11"];
    }

    get upperLeftTeeth() {
        if (this.state.dentitionType === "primary") {
            return ["61", "62", "63", "64", "65"];
        } else if (this.state.dentitionType === "mixed") {
            return ["21", "22", "63", "64", "65", "26"];
        }
        return ["21", "22", "23", "24", "25", "26", "27", "28"];
    }

    get lowerLeftTeeth() {
        if (this.state.dentitionType === "primary") {
            return ["75", "74", "73", "72", "71"];
        } else if (this.state.dentitionType === "mixed") {
            return ["31", "32", "73", "74", "75", "36"];
        }
        return ["38", "37", "36", "35", "34", "33", "32", "31"];
    }

    get lowerRightTeeth() {
        if (this.state.dentitionType === "primary") {
            return ["85", "84", "83", "82", "81"];
        } else if (this.state.dentitionType === "mixed") {
            return ["46", "85", "84", "83", "42", "41"];
        }
        return ["48", "47", "46", "45", "44", "43", "42", "41"];
    }

    get allTeethList() {
        const allNums = [
            ...this.upperRightTeeth,
            ...this.upperLeftTeeth,
            ...this.lowerRightTeeth,
            ...this.lowerLeftTeeth,
        ];
        return allNums.map((tn) => {
            const d = this.state.teeth[tn] || {};
            return {
                number: tn,
                name: d.tooth_name || `Tooth ${tn}`,
                condition: d.condition || "sound",
            };
        });
    }

    get selectedToothData() {
        const tn = this.state.selectedTooth;
        if (!tn || !this.state.teeth[tn]) {
            return {
                tooth_name: _t("Select Tooth"),
                condition: "sound",
                surfaces: "",
                severity: "",
                universal_number: "",
                palmer_notation: "",
                history: [],
                diagnoses: [],
                proposed_treatments: [],
                completed_treatments: [],
                sessions: [],
            };
        }
        return this.state.teeth[tn];
    }

    get selectedToothHistory() {
        return this.selectedToothData.history || [];
    }

    get selectedToothDiagnoses() {
        return this.selectedToothData.diagnoses || [];
    }

    get selectedToothTreatments() {
        return this.selectedToothData.proposed_treatments || [];
    }

    get selectedToothCompletedTreatments() {
        return this.selectedToothData.completed_treatments || [];
    }

    get selectedToothSessions() {
        return this.selectedToothData.sessions || [];
    }

    isSurfaceAffected(surf) {
        const tn = this.state.selectedTooth;
        if (!tn || !this.state.teeth[tn]) return false;
        const currentData = this.state.teeth[tn];
        const s = currentData.surfaces || "";
        return s.toUpperCase().includes(surf.toUpperCase());
    }

    getConditionLabel(cond) {
        const labels = {
            sound: _t("Sound / Healthy"),
            caries: _t("Caries / Cavity"),
            restoration: _t("Restoration / Filled"),
            crown: _t("Crown / Cap"),
            root_canal: _t("Root Canal Treated"),
            implant: _t("Dental Implant"),
            missing: _t("Missing Tooth"),
            fracture: _t("Fracture / Chipped"),
            impacted: _t("Impacted"),
            extraction_indicated: _t("Extraction Indicated"),
            bridge: _t("Bridge Pontic"),
            other: _t("Other Finding"),
        };
        return labels[cond] || cond || _t("Sound");
    }

    getToothStripClasses(tNum) {
        const cond = this.state.teeth[tNum]?.condition || "sound";
        const isActive = this.state.selectedTooth === tNum;
        return {
            active: isActive,
            [`cond-${cond}`]: true,
        };
    }

    // -------------------------------------------------------------------------
    // Odontogram Data Fetching & State
    // -------------------------------------------------------------------------

    async loadOdontogram() {
        const patientId = this.patientId || this.getPatientId();
        const caseId = this.caseId || this.getCaseId();

        if (!patientId) {
            this.state.patientName = "";
            this.state.patientRef = "";
            this.state.teeth = {};
            this.state.stats = { sound: 32, caries: 0, restoration: 0, missing: 0, other: 0 };
            this.updateAllToothMaterials();
            return;
        }

        try {
            const data = await this.orm.call("dental.case", "get_odontogram_data", [caseId || []], {
                patient_id: patientId,
            });

            this.state.patientId = data.patient_id;
            this.state.patientName = data.patient_name;
            this.state.patientRef = data.patient_ref;
            this.state.patientAge = data.patient_age;
            this.state.patientDob = data.patient_dob;
            this.state.suggestedDentition = data.suggested_dentition || "permanent";
            
            // Only auto-set dentitionType if user hasn't explicitly customized it, or on initial load
            if (!this.userOverrodeDentition) {
                this.state.dentitionType = this.state.suggestedDentition;
            }

            this.state.caseId = data.case_id;
            this.state.caseName = data.case_name;
            this.state.canEdit = data.can_edit;
            this.state.isDentist = data.is_dentist;
            this.state.teeth = data.teeth || {};
            this.state.stats = data.stats || {};
            this.state.diagnosisMasters = data.diagnosis_masters || [];

            if (this.state.canEdit && !this.state.activePanelTab) {
                this.state.activePanelTab = "record";
            } else if (!this.state.canEdit) {
                this.state.activePanelTab = "history";
            }

            this.applyDentitionVisibility();
            this.updateAllToothMaterials();
        } catch (error) {
            console.error("Failed to load odontogram data:", error);
        }
    }

    // -------------------------------------------------------------------------
    // Dynamic 3D Asset & Library Loading
    // -------------------------------------------------------------------------

    async ensure3DLibraries() {
        if (!window.MeshoptDecoder) {
            await this.loadScript("/dental_core/static/lib/meshopt_decoder.js");
        }
        if (window.MeshoptDecoder && window.MeshoptDecoder.ready) {
            await window.MeshoptDecoder.ready;
        }
        if (!window.THREE?.GLTFLoader) {
            await this.loadScript("/dental_core/static/lib/GLTFLoader.js");
        }
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            const existing = document.querySelector(`script[src="${src}"]`);
            if (existing) {
                if (existing.dataset.loaded === "true" || window.MeshoptDecoder || window.THREE?.GLTFLoader) {
                    return resolve();
                }
                existing.addEventListener("load", () => resolve());
                existing.addEventListener("error", (e) => reject(e));
                return;
            }
            const script = document.createElement("script");
            script.src = src;
            script.async = true;
            script.onload = () => {
                script.dataset.loaded = "true";
                resolve();
            };
            script.onerror = (e) => reject(e);
            document.head.appendChild(script);
        });
    }

    // -------------------------------------------------------------------------
    // 3D Scene Initialization
    // -------------------------------------------------------------------------

    async init3DScene() {
        if (this.is3DReady) return;
        const THREE = window.THREE;
        if (!THREE) {
            console.error("Three.js library is not available.");
            return;
        }

        const container = this.containerEl;
        if (!container) return;

        const viewport = this.viewportEl;
        const width = container.clientWidth > 50 ? container.clientWidth : (viewport?.clientWidth || 700);
        const height = container.clientHeight > 50 ? container.clientHeight : (viewport?.clientHeight || 500);

        // 1. Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf8fafc); // Clean modern healthcare light neutral

        // 2. Camera: Centered framing for anatomical dental model
        this.camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 1000);
        this.camera.position.set(0, 0.2, 11.2);

        // 3. Renderer with high-quality soft shadows & tone mapping
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        if (THREE.sRGBEncoding) {
            this.renderer.outputEncoding = THREE.sRGBEncoding;
        }
        if (THREE.ACESFilmicToneMapping) {
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            this.renderer.toneMappingExposure = 1.05;
        }
        container.innerHTML = "";
        container.appendChild(this.renderer.domElement);

        // 4. Studio Lighting (Key, Fill, Rim, Ambient)
        this.setupLighting(THREE);

        // 5. Controls
        if (THREE.OrbitControls) {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.08;
            this.controls.maxDistance = 24;
            this.controls.minDistance = 3.5;
            this.controls.target.set(0, -0.15, 0);
        }

        // 6. Raycaster
        this.raycaster = new THREE.Raycaster();
        this.pointer = new THREE.Vector2();
        this.pointerDownPos = { x: 0, y: 0 };

        // 7. Ground Contact Shadow Plane
        const shadowPlane = new THREE.Mesh(
            new THREE.PlaneGeometry(32, 32),
            new THREE.ShadowMaterial({ opacity: 0.08 })
        );
        shadowPlane.rotation.x = -Math.PI / 2;
        shadowPlane.position.y = -4.2;
        shadowPlane.receiveShadow = true;
        this.scene.add(shadowPlane);

        // 8. Event Listeners
        this.renderer.domElement.addEventListener("pointerdown", (e) => {
            this.pointerDownPos = { x: e.clientX, y: e.clientY };
        });
        this.renderer.domElement.addEventListener("pointermove", (e) => this.onPointerMove(e));
        this.renderer.domElement.addEventListener("pointerup", (e) => this.onPointerUp(e));
        this.renderer.domElement.addEventListener("click", (e) => this.onPointerUp(e));

        // 9. Observers for dynamic tabs & responsiveness
        if (window.ResizeObserver && viewport) {
            this.resizeObserver = new ResizeObserver(() => {
                this.onWindowResize();
            });
            this.resizeObserver.observe(viewport);
        }

        if (window.IntersectionObserver && viewport) {
            this.intersectionObserver = new IntersectionObserver((entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        this.onWindowResize();
                    }
                }
            });
            this.intersectionObserver.observe(viewport);
        }

        const tabPane = container.closest(".tab-pane") || container.closest(".o_group");
        if (tabPane) {
            this.tabMutationObserver = new MutationObserver(() => {
                this.onWindowResize();
            });
            this.tabMutationObserver.observe(tabPane, { attributes: true, attributeFilter: ["class", "style"] });
        }

        window.addEventListener("resize", (this.onWindowResizeBound = () => this.onWindowResize()));

        // 10. Start Animation Loop
        this.is3DReady = true;
        const animate = () => {
            this.animationFrameId = requestAnimationFrame(animate);
            if (this.controls) this.controls.update();
            this.renderer.render(this.scene, this.camera);
        };
        animate();

        // 11. Load Anatomically Realistic Dental Model
        await this.loadDentalModel(THREE);
    }

    setupLighting(THREE) {
        // Balanced ambient base
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.72);
        this.scene.add(ambientLight);

        // Warm directional key light
        const keyLight = new THREE.DirectionalLight(0xfffbf5, 0.84);
        keyLight.position.set(6, 14, 11);
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 2048;
        keyLight.shadow.mapSize.height = 2048;
        keyLight.shadow.bias = -0.0001;
        this.scene.add(keyLight);

        // Cool clinical fill light
        const fillLight = new THREE.DirectionalLight(0xe2e8f0, 0.42);
        fillLight.position.set(-7, -4, 9);
        this.scene.add(fillLight);

        // Rim highlight from top-back for enamel and mucosal contours
        const rimLight = new THREE.DirectionalLight(0xffffff, 0.32);
        rimLight.position.set(0, 10, -11);
        this.scene.add(rimLight);

        // Hemisphere light
        const hemiLight = new THREE.HemisphereLight(0xffffff, 0x94a3b8, 0.38);
        this.scene.add(hemiLight);
    }

    // -------------------------------------------------------------------------
    // Realistic Model Loading & Arch Composition
    // -------------------------------------------------------------------------

    async loadDentalModel(THREE) {
        this.state.isLoadingModel = true;
        try {
            await this.ensure3DLibraries();

            if (!THREE.GLTFLoader) {
                throw new Error("GLTFLoader is not available.");
            }

            const loader = new THREE.GLTFLoader();
            if (window.MeshoptDecoder) {
                loader.setMeshoptDecoder(window.MeshoptDecoder);
            }

            loader.load(
                "/dental_core/static/models/dental_arch.glb",
                (gltf) => {
                    this.onModelLoaded(THREE, gltf);
                    this.state.isLoadingModel = false;
                    this.updateAllToothMaterials();
                },
                undefined,
                (error) => {
                    console.error("Failed to load anatomical GLB model, falling back to procedural arches:", error);
                    this.buildProceduralDentalArches(THREE);
                    this.state.isLoadingModel = false;
                    this.updateAllToothMaterials();
                }
            );
        } catch (err) {
            console.error("Error initializing 3D model loader:", err);
            this.buildProceduralDentalArches(THREE);
            this.state.isLoadingModel = false;
            this.updateAllToothMaterials();
        }
    }

    onModelLoaded(THREE, gltf) {
        if (this.modelRoot) {
            this.scene.remove(this.modelRoot);
        }
        this.toothMeshes = {};

        this.modelRoot = new THREE.Group();
        this.upperJawGroup = new THREE.Group();
        this.lowerJawGroup = new THREE.Group();
        this.modelRoot.add(this.upperJawGroup);
        this.modelRoot.add(this.lowerJawGroup);

        // Realistic gingival tissue materials (natural soft pink mucosal tissue)
        const gumMatUpper = new THREE.MeshStandardMaterial({
            color: 0xdf8490,
            roughness: 0.38,
            metalness: 0.02,
            side: THREE.DoubleSide,
        });

        const gumMatLower = new THREE.MeshStandardMaterial({
            color: 0xdf8490,
            roughness: 0.38,
            metalness: 0.02,
            side: THREE.DoubleSide,
        });

        const upperToothNames = new Set([
            "tooth-18", "tooth-17", "tooth-16", "tooth-15", "tooth-14", "tooth-13", "tooth-12", "tooth-11",
            "tooth-21", "tooth-22", "tooth-23", "tooth-24", "tooth-25", "tooth-26", "tooth-27", "tooth-28"
        ]);
        const lowerToothNames = new Set([
            "tooth-48", "tooth-47", "tooth-46", "tooth-45", "tooth-44", "tooth-43", "tooth-42", "tooth-41",
            "tooth-31", "tooth-32", "tooth-33", "tooth-34", "tooth-35", "tooth-36", "tooth-37", "tooth-38"
        ]);

        const nodesToProcess = [];
        gltf.scene.traverse((child) => {
            if (child.isMesh) {
                nodesToProcess.push(child);
            }
        });

        for (const mesh of nodesToProcess) {
            const name = mesh.name;
            mesh.castShadow = true;
            mesh.receiveShadow = true;

            // KHR_mesh_quantization: un-quantize vertex positions & normals from Int16 to standard Float32
            // Three.js CPU Raycaster and bounding calculations require actual Float32 coordinates.
            // Using posAttr.getX/Y/Z(i) correctly decodes interleaved/strided buffers without vertex corruption!
            if (mesh.geometry && mesh.geometry.attributes.position) {
                const posAttr = mesh.geometry.attributes.position;
                if (posAttr.normalized && (posAttr.array instanceof Int16Array || posAttr.isInterleavedBufferAttribute)) {
                    const count = posAttr.count;
                    const floatPositions = new Float32Array(count * 3);
                    for (let i = 0; i < count; i++) {
                        floatPositions[i * 3 + 0] = Math.max(posAttr.getX(i) / 32767.0, -1.0);
                        floatPositions[i * 3 + 1] = Math.max(posAttr.getY(i) / 32767.0, -1.0);
                        floatPositions[i * 3 + 2] = Math.max(posAttr.getZ(i) / 32767.0, -1.0);
                    }
                    mesh.geometry.setAttribute("position", new THREE.BufferAttribute(floatPositions, 3, false));
                }
                const normAttr = mesh.geometry.attributes.normal;
                if (normAttr && normAttr.normalized && (normAttr.array instanceof Int16Array || normAttr.isInterleavedBufferAttribute)) {
                    const count = normAttr.count;
                    const floatNormals = new Float32Array(count * 3);
                    for (let i = 0; i < count; i++) {
                        floatNormals[i * 3 + 0] = Math.max(normAttr.getX(i) / 32767.0, -1.0);
                        floatNormals[i * 3 + 1] = Math.max(normAttr.getY(i) / 32767.0, -1.0);
                        floatNormals[i * 3 + 2] = Math.max(normAttr.getZ(i) / 32767.0, -1.0);
                    }
                    mesh.geometry.setAttribute("normal", new THREE.BufferAttribute(floatNormals, 3, false));
                }
                mesh.geometry.computeBoundingBox();
                mesh.geometry.computeBoundingSphere();
                if (!mesh.geometry.attributes.normal || name.includes("gingiva")) {
                    mesh.geometry.computeVertexNormals();
                }
            }

            if (name === "gingiva-upper") {
                mesh.material = gumMatUpper;
                this.upperJawGroup.add(mesh);
            } else if (name === "gingiva-lower") {
                mesh.material = gumMatLower;
                this.lowerJawGroup.add(mesh);
            } else if (upperToothNames.has(name)) {
                const toothNum = name.replace("tooth-", "");
                const toothMat = new THREE.MeshStandardMaterial({
                    color: 0xf8f6f0, // Natural pearlescent ivory enamel
                    roughness: 0.20,
                    metalness: 0.02,
                    side: THREE.DoubleSide,
                });
                mesh.material = toothMat;
                mesh.userData = { toothNumber: toothNum, isUpper: true };
                this.upperJawGroup.add(mesh);

                this.toothMeshes[toothNum] = {
                    mesh: mesh,
                    isUpper: true,
                    basePos: mesh.position.clone(),
                    toothNumber: toothNum,
                };
            } else if (lowerToothNames.has(name)) {
                const toothNum = name.replace("tooth-", "");
                const toothMat = new THREE.MeshStandardMaterial({
                    color: 0xf8f6f0,
                    roughness: 0.20,
                    metalness: 0.02,
                    side: THREE.DoubleSide,
                });
                mesh.material = toothMat;
                mesh.userData = { toothNumber: toothNum, isUpper: false };
                this.lowerJawGroup.add(mesh);

                this.toothMeshes[toothNum] = {
                    mesh: mesh,
                    isUpper: false,
                    basePos: mesh.position.clone(),
                    toothNumber: toothNum,
                };
            } else {
                // Non-arch bone and sinus structures hidden to maintain pristine dental arch focus
                mesh.visible = false;
            }
        }

        // Also register pediatric deciduous tooth numbers to corresponding anatomical tooth meshes
        const primaryToAdultMap = {
            "55": "16", "54": "14", "53": "13", "52": "12", "51": "11",
            "61": "21", "62": "22", "63": "23", "64": "24", "65": "26",
            "71": "31", "72": "32", "73": "33", "74": "34", "75": "36",
            "81": "41", "82": "42", "83": "43", "84": "44", "85": "46",
        };
        for (const [pNum, aNum] of Object.entries(primaryToAdultMap)) {
            if (this.toothMeshes[aNum]) {
                this.toothMeshes[pNum] = {
                    mesh: this.toothMeshes[aNum].mesh,
                    isUpper: this.toothMeshes[aNum].isUpper,
                    basePos: this.toothMeshes[aNum].basePos,
                    toothNumber: pNum,
                    isPrimary: true,
                };
            }
        }

        // Add Anatomical 3D Tongue nestled comfortably inside the mandibular arch
        const tongueMesh = this.createTongueMesh(THREE);
        this.lowerJawGroup.add(tongueMesh);

        // Separate upper and lower jaws with balanced natural open bite centered in viewport
        // Upper Maxillary Arch: Raised slightly up and leveled
        this.upperJawGroup.position.set(0, 0.42, 0.0);
        this.upperJawGroup.rotation.x = -0.02;

        // Lower Mandibular Arch: Lowered slightly down and leveled
        this.lowerJawGroup.position.set(0, -0.42, 0.0);
        this.lowerJawGroup.rotation.x = 0.02;

        // Center the composite jaws vertically in the viewport
        this.modelRoot.position.set(0, -0.10, 0.1);
        this.scene.add(this.modelRoot);

        // Force full world matrix computation so raycaster hits exact tooth positions immediately
        this.modelRoot.updateMatrixWorld(true);

        this.applyDentitionVisibility();
    }

    createTongueMesh(THREE) {
        const uSegs = 32;
        const vSegs = 32;
        const positions = [];
        const indices = [];
        const uvs = [];

        for (let i = 0; i <= vSegs; i++) {
            const v = i / vSegs; // 0 (tip) to 1 (posterior root)
            const z = 1.05 - v * 3.2;
            const w = 1.40 * Math.sin(Math.PI * Math.pow(v, 0.45)); // Anatomical width

            for (let j = 0; j <= uSegs; j++) {
                const u = (j / uSegs) * 2 - 1; // -1 to +1
                const x = u * w;

                // Dome height nestled below occlusal table
                const hBase = 0.48 * Math.sin(Math.PI * Math.pow(v, 0.55)) * Math.max(0, 1.0 - u * u);
                const sulcus = 0.05 * Math.exp(-12.0 * u * u) * Math.sin(Math.PI * v);
                const y = -1.55 + Math.max(0, hBase - sulcus);

                positions.push(x, y, z);
                uvs.push(j / uSegs, v);
            }
        }

        for (let i = 0; i < vSegs; i++) {
            for (let j = 0; j < uSegs; j++) {
                const a = i * (uSegs + 1) + j;
                const b = (i + 1) * (uSegs + 1) + j;
                const c = (i + 1) * (uSegs + 1) + (j + 1);
                const d = i * (uSegs + 1) + (j + 1);
                indices.push(a, b, d);
                indices.push(b, c, d);
            }
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
        geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
        geo.setIndex(indices);
        geo.computeVertexNormals();

        const mat = new THREE.MeshStandardMaterial({
            color: 0xba5464, // Healthy moist tongue mucosal tone
            roughness: 0.45, // Soft organic sheen
            metalness: 0.02,
            side: THREE.DoubleSide,
        });

        const mesh = new THREE.Mesh(geo, mat);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return mesh;
    }

    // -------------------------------------------------------------------------
    // Fallback Procedural Arches (if GLB asset is unavailable)
    // -------------------------------------------------------------------------

    buildProceduralDentalArches(THREE) {
        this.toothMeshes = {};
        const archRadiusX = 5.6;
        const archRadiusZ = 6.4;

        const upperTeeth = [
            "18", "17", "16", "15", "14", "13", "12", "11",
            "21", "22", "23", "24", "25", "26", "27", "28"
        ];
        this.createProceduralArch(THREE, upperTeeth, +1.75, true, archRadiusX, archRadiusZ);

        const lowerTeeth = [
            "48", "47", "46", "45", "44", "43", "42", "41",
            "31", "32", "33", "34", "35", "36", "37", "38"
        ];
        this.createProceduralArch(THREE, lowerTeeth, -1.75, false, archRadiusX * 0.94, archRadiusZ * 0.94);
    }

    createProceduralArch(THREE, teethList, yLevel, isUpper, radiusX, radiusZ) {
        const count = teethList.length;
        const angleStep = (Math.PI * 0.96) / (count - 1);

        for (let i = 0; i < count; i++) {
            const toothNum = teethList[i];
            const theta = -Math.PI * 0.48 + i * angleStep;

            const posX = radiusX * Math.sin(theta);
            const posZ = -radiusZ * (1 - Math.cos(theta)) + 1.4;

            const toothGroup = new THREE.Group();
            toothGroup.position.set(posX, yLevel, posZ);
            toothGroup.rotation.y = -theta;
            if (!isUpper) toothGroup.rotation.z = Math.PI;

            const crownGeo = new THREE.CylinderGeometry(0.65, 0.55, 0.95, 16);
            const crownMat = new THREE.MeshStandardMaterial({ color: 0xf5f2ec, roughness: 0.22, metalness: 0.04 });
            const crownMesh = new THREE.Mesh(crownGeo, crownMat);
            crownMesh.castShadow = true;
            crownMesh.receiveShadow = true;
            crownMesh.userData = { toothNumber: toothNum, isUpper };
            toothGroup.add(crownMesh);

            this.scene.add(toothGroup);

            this.toothMeshes[toothNum] = {
                mesh: crownMesh,
                group: toothGroup,
                isUpper: isUpper,
                basePos: crownMesh.position.clone(),
                toothNumber: toothNum,
            };
        }
    }

    // -------------------------------------------------------------------------
    // Material Updates & Condition Color Coding
    // -------------------------------------------------------------------------

    updateAllToothMaterials() {
        if (!this.is3DReady) return;
        const THREE = window.THREE;
        if (!THREE) return;

        const conditionColors = {
            sound: 0xfcfbfa,                // Natural pearlescent translucent enamel
            caries: 0xef4444,               // Alert red (Caries/Cavity)
            restoration: 0x3b82f6,          // Clinical blue (Filled/Restoration)
            crown: 0xf59e0b,               // Lustrous gold (Crown)
            root_canal: 0xa855f7,           // Deep violet (Endodontic)
            implant: 0x06b6d4,              // Titanium cyan (Implant)
            missing: 0x94a3b8,              // Ghost slate (Missing)
            fracture: 0xf97316,             // Alert orange (Chipped/Fracture)
            impacted: 0xec4899,             // Pink (Impacted)
            extraction_indicated: 0xdc2626, // Crimson (Extraction)
            bridge: 0x6366f1,               // Indigo (Bridge)
            other: 0x64748b,                // Muted grey (Other)
        };

        for (const [tNum, toothObj] of Object.entries(this.toothMeshes)) {
            // Only iterate anatomical primary meshes (skip duplicate deciduous pointer objects)
            if (toothObj.isPrimary) continue;

            const activeNum = this.getActiveToothNumber(tNum);
            const toothInfo = this.state.teeth[activeNum] || { condition: "sound" };
            const cond = toothInfo.condition || "sound";
            const isSelected = this.state.selectedTooth === activeNum;
            const isHovered = this.state.hoveredTooth === activeNum;

            const colorHex = conditionColors[cond] || conditionColors.sound;
            const mesh = toothObj.mesh;
            if (!mesh || !mesh.material) continue;

            mesh.material.color.setHex(colorHex);

            if (cond === "missing") {
                mesh.material.transparent = true;
                mesh.material.opacity = 0.18;
                mesh.material.wireframe = true;
            } else {
                mesh.material.transparent = false;
                mesh.material.opacity = 1.0;
                mesh.material.wireframe = false;
            }

            if (cond === "crown") {
                mesh.material.metalness = 0.72;
                mesh.material.roughness = 0.22;
            } else if (cond === "implant") {
                mesh.material.metalness = 0.85;
                mesh.material.roughness = 0.20;
            } else {
                mesh.material.metalness = 0.02;
                mesh.material.roughness = cond === "caries" ? 0.38 : 0.16;
            }

            mesh.material.side = THREE.DoubleSide;

            // Selection & Hover Emissive Highlighting - Clear visibility without obscuring condition color
            if (isSelected) {
                // If the tooth has a clinical condition (like Caries, Crown, etc.), enhance that condition color!
                // If it's sound/default, provide a clean soft highlight with the socket lift
                if (cond === "sound") {
                    mesh.material.emissive.setHex(0x0284c7);
                    mesh.material.emissiveIntensity = 0.28;
                } else {
                    // Accentuate the condition's own color with subtle glow so Caries remains brilliant red, Crown gold, etc.
                    mesh.material.emissive.setHex(colorHex);
                    mesh.material.emissiveIntensity = 0.32;
                }

                // Tactile lift out of socket for instant visual confirmation
                if (toothObj.basePos) {
                    const liftY = toothObj.isUpper ? 0.28 : -0.28;
                    mesh.position.y = toothObj.basePos.y + liftY;
                    mesh.position.z = toothObj.basePos.z + 0.18;
                }
            } else if (isHovered) {
                if (cond === "sound") {
                    mesh.material.emissive.setHex(0x38bdf8);
                    mesh.material.emissiveIntensity = 0.22;
                } else {
                    mesh.material.emissive.setHex(colorHex);
                    mesh.material.emissiveIntensity = 0.22;
                }
                if (toothObj.basePos) {
                    mesh.position.copy(toothObj.basePos);
                }
            } else {
                mesh.material.emissive.setHex(0x000000);
                mesh.material.emissiveIntensity = 0.0;
                if (toothObj.basePos) {
                    mesh.position.copy(toothObj.basePos);
                }
            }
        }
    }

    getActiveToothNumber(adultToothNum) {
        const dentition = this.state.dentitionType || "permanent";
        if (dentition === "primary") {
            const adultToPrimaryMap = {
                "16": "55", "14": "54", "13": "53", "12": "52", "11": "51",
                "21": "61", "22": "62", "23": "63", "24": "64", "26": "65",
                "31": "71", "32": "72", "33": "73", "34": "74", "36": "75",
                "41": "81", "42": "82", "43": "83", "44": "84", "46": "85",
            };
            return adultToPrimaryMap[adultToothNum] || adultToothNum;
        } else if (dentition === "mixed") {
            const mixedAdultToDeciduous = {
                "14": "54", "13": "53",
                "23": "63", "24": "64", "25": "65",
                "33": "73", "34": "74", "35": "75",
                "43": "83", "44": "84", "45": "85",
            };
            return mixedAdultToDeciduous[adultToothNum] || adultToothNum;
        }
        return adultToothNum;
    }

    // -------------------------------------------------------------------------
    // Raycasting & User Interactions
    // -------------------------------------------------------------------------

    getInteractiveMeshes() {
        const uniqueMeshes = [];
        const seen = new Set();
        for (const tObj of Object.values(this.toothMeshes || {})) {
            if (tObj && tObj.mesh && tObj.mesh.visible && !seen.has(tObj.mesh)) {
                seen.add(tObj.mesh);
                uniqueMeshes.push(tObj.mesh);
            }
        }
        return uniqueMeshes;
    }

    findIntersectedTooth(event) {
        if (!this.is3DReady || !this.renderer || !this.camera) return null;

        const rect = this.renderer.domElement.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return null;

        const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.pointer.set(x, y);
        this.raycaster.setFromCamera(this.pointer, this.camera);

        const interactiveMeshes = this.getInteractiveMeshes();
        if (interactiveMeshes.length === 0) return null;

        // Ensure world matrices are fresh for raycaster
        for (let i = 0; i < interactiveMeshes.length; i++) {
            interactiveMeshes[i].updateMatrixWorld();
        }

        const intersects = this.raycaster.intersectObjects(interactiveMeshes, true);
        if (intersects.length > 0) {
            // Find first intersection with a tooth number
            for (const hitObj of intersects) {
                let curr = hitObj.object;
                while (curr && curr !== this.scene) {
                    const tNum = curr.userData?.toothNumber;
                    if (tNum) {
                        const activeNum = this.getActiveToothNumber(String(tNum));
                        return { toothNumber: activeNum, object: curr, rect };
                    }
                    curr = curr.parent;
                }
            }
        }
        return null;
    }

    onPointerMove(event) {
        if (!this.is3DReady || !this.renderer) return;

        const result = this.findIntersectedTooth(event);
        if (result) {
            const { toothNumber, rect } = result;
            this.renderer.domElement.style.cursor = "pointer";
            const info = this.state.teeth[toothNumber];
            const condLabel = this.getConditionLabel(info?.condition || "sound");
            if (this.state.hoveredTooth !== toothNumber) {
                this.state.hoveredTooth = toothNumber;
                this.state.hoveredToothInfo = `Tooth ${toothNumber} • ${condLabel}`;
                this.updateAllToothMaterials();
            }
            this.state.tooltipX = event.clientX - rect.left;
            this.state.tooltipY = event.clientY - rect.top;
            return;
        }

        if (this.state.hoveredTooth) {
            this.renderer.domElement.style.cursor = "grab";
            this.state.hoveredTooth = null;
            this.updateAllToothMaterials();
        }
    }

    onPointerUp(event) {
        if (!this.is3DReady || !this.renderer) return;

        // Check if movement between pointer down and up was small (a clean click / tap)
        const dx = event.clientX - (this.pointerDownPos?.x ?? event.clientX);
        const dy = event.clientY - (this.pointerDownPos?.y ?? event.clientY);
        const dragDist = Math.hypot(dx, dy);
        if (dragDist > 16) return; // User was deliberately orbiting or panning

        const result = this.findIntersectedTooth(event);
        if (result) {
            this.selectTooth(result.toothNumber);
        }
    }

    selectTooth(tNum) {
        if (!tNum) return;
        this.state.selectedTooth = String(tNum);
        const currentData = this.state.teeth[this.state.selectedTooth];

        // Prepopulate new finding form with current finding defaults
        if (currentData) {
            this.state.newFinding.condition = currentData.condition === "sound" ? "caries" : currentData.condition;
            this.state.newFinding.diagnosis_id = "";
            this.state.newFinding.surfaces = currentData.surfaces ? currentData.surfaces.split("") : ["O"];
            this.state.newFinding.severity = currentData.severity || "moderate";
            this.state.newFinding.treatment_indicated = currentData.treatment_indicated || "";
            this.state.newFinding.notes = "";
        } else {
            this.state.newFinding.condition = "caries";
            this.state.newFinding.diagnosis_id = "";
            this.state.newFinding.surfaces = ["O"];
            this.state.newFinding.severity = "moderate";
            this.state.newFinding.treatment_indicated = "";
            this.state.newFinding.notes = "";
        }

        if (this.state.canEdit) {
            this.state.activePanelTab = "record";
        } else {
            this.state.activePanelTab = "history";
        }

        this.updateAllToothMaterials();
    }

    // -------------------------------------------------------------------------
    // View Controls & Camera Presets
    // -------------------------------------------------------------------------

    setView(viewName) {
        if (!this.camera || !this.controls) return;
        this.state.currentView = viewName;

        if (viewName === "front") {
            // Anterior front bite overview
            this.camera.position.set(0, 0.2, 11.2);
            this.controls.target.set(0, -0.10, 0);
        } else if (viewName === "upper") {
            // Maxilla view looking up from anterior-inferior at palatal curvature
            this.camera.position.set(0, -6.0, 7.5);
            this.controls.target.set(0, 0.45, 0.2);
        } else if (viewName === "lower") {
            // Mandible view looking down from anterior-superior at teeth & arch
            this.camera.position.set(0, 6.5, 7.0);
            this.controls.target.set(0, -0.45, 0.2);
        } else if (viewName === "occlusal") {
            // Angled 3D occlusal overview
            this.camera.position.set(0, 5.2, 9.8);
            this.controls.target.set(0, -0.10, 0);
        }
        this.controls.update();
    }

    resetCamera() {
        this.setView("front");
    }

    zoomCamera(delta) {
        if (!this.camera || !this.controls) return;
        const target = this.controls.target;
        const offset = this.camera.position.clone().sub(target);
        const factor = delta > 0 ? 1.15 : 0.85;
        offset.multiplyScalar(factor);
        const dist = offset.length();
        if (dist >= this.controls.minDistance && dist <= this.controls.maxDistance) {
            this.camera.position.copy(target).add(offset);
            this.controls.update();
        }
    }

    rotateCamera(angleDelta) {
        if (!this.camera || !this.controls) return;
        const target = this.controls.target;
        const offset = this.camera.position.clone().sub(target);
        const cos = Math.cos(angleDelta);
        const sin = Math.sin(angleDelta);
        const newX = offset.x * cos - offset.z * sin;
        const newZ = offset.x * sin + offset.z * cos;
        this.camera.position.set(target.x + newX, this.camera.position.y, target.z + newZ);
        this.camera.lookAt(target);
        this.controls.update();
    }

    panCamera(deltaX, deltaY) {
        if (!this.camera || !this.controls) return;
        this.camera.position.x += deltaX;
        this.camera.position.y += deltaY;
        this.controls.target.x += deltaX;
        this.controls.target.y += deltaY;
        this.controls.update();
    }

    setDentitionType(type) {
        this.userOverrodeDentition = true;
        this.state.dentitionType = type;
        this.state.selectedTooth = null;
        this.applyDentitionVisibility();
        this.updateAllToothMaterials();
    }

    applyDentitionVisibility() {
        if (!this.toothMeshes) return;
        const dentition = this.state.dentitionType || "permanent";

        // Permanent: all 32 adult teeth visible
        // Primary: 20 deciduous teeth (FDI 51-55, 61-65, 71-75, 81-85).
        // In 3D jaw model, 20 teeth corresponds to anterior 5 teeth of each quadrant (excluding 18, 17, 27, 28, 38, 37, 47, 48, 15, 25, 35, 45)
        const primaryHiddenAdult = new Set([
            "18", "17", "15",
            "28", "27", "25",
            "38", "37", "35",
            "48", "47", "45",
        ]);

        // Mixed: 24 teeth (6 in each quadrant: permanent 1st molars 16, 26, 36, 46 + primary molars & incisors; excluding 3rd & 2nd permanent molars)
        const mixedHiddenAdult = new Set([
            "18", "17", "28", "27", "38", "37", "48", "47"
        ]);

        for (const [tNum, toothObj] of Object.entries(this.toothMeshes)) {
            if (!toothObj || !toothObj.mesh) continue;
            if (toothObj.isPrimary) continue; // Deciduous entries point to same underlying mesh

            if (dentition === "primary") {
                toothObj.mesh.visible = !primaryHiddenAdult.has(tNum);
            } else if (dentition === "mixed") {
                toothObj.mesh.visible = !mixedHiddenAdult.has(tNum);
            } else {
                toothObj.mesh.visible = true;
            }
        }
    }

    onWindowResize() {
        if (!this.is3DReady) {
            this.init3DScene();
            return;
        }
        const viewport = this.viewportEl;
        if (!viewport || !this.camera || !this.renderer) return;
        const width = viewport.clientWidth;
        const height = viewport.clientHeight;
        if (width > 50 && height > 50) {
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
            if (this.controls) this.controls.update();
        }
    }

    // -------------------------------------------------------------------------
    // Panel Form Actions (Record Finding)
    // -------------------------------------------------------------------------

    setPanelTab(tabName) {
        this.state.activePanelTab = tabName;
    }

    hasSurface(surf) {
        return this.state.newFinding.surfaces.includes(surf);
    }

    toggleSurface(surf) {
        const idx = this.state.newFinding.surfaces.indexOf(surf);
        if (idx >= 0) {
            this.state.newFinding.surfaces.splice(idx, 1);
        } else {
            this.state.newFinding.surfaces.push(surf);
        }
    }

    setSeverity(sev) {
        this.state.newFinding.severity = sev;
    }

    setCondition(val) {
        this.state.newFinding.condition = val;
        const tNum = this.state.selectedTooth;
        if (tNum) {
            if (!this.state.teeth[tNum]) {
                this.state.teeth[tNum] = {
                    tooth_number: tNum,
                    condition: val,
                    surfaces: this.state.newFinding.surfaces.join(""),
                    severity: this.state.newFinding.severity,
                };
            } else {
                this.state.teeth[tNum].condition = val;
            }
            this.updateAllToothMaterials();
        }
    }

    async quickApplyCondition(cond) {
        if (!this.state.selectedTooth) return;
        this.setCondition(cond);
        if (cond === "sound") {
            await this.onClearFinding();
        } else {
            await this.onSaveFinding();
        }
    }

    setDiagnosis(val) {
        this.state.newFinding.diagnosis_id = val;
    }

    setTreatmentIndicated(val) {
        this.state.newFinding.treatment_indicated = val;
    }

    setNotes(val) {
        this.state.newFinding.notes = val;
    }

    async onSaveFinding() {
        if (!this.state.selectedTooth) return;
        const caseId = this.caseId || this.getCaseId();
        if (!caseId) {
            this.notification.add(_t("Please save the dental case before recording findings."), {
                type: "warning",
            });
            return;
        }

        this.state.isSaving = true;

        try {
            const result = await this.orm.call("dental.case", "save_tooth_finding", [caseId], {
                tooth_data: {
                    tooth_number: this.state.selectedTooth,
                    condition: this.state.newFinding.condition,
                    diagnosis_id: this.state.newFinding.diagnosis_id || false,
                    surfaces: this.state.newFinding.surfaces.join(""),
                    severity: this.state.newFinding.severity,
                    treatment_indicated: this.state.newFinding.treatment_indicated,
                    notes: this.state.newFinding.notes,
                },
            });

            if (result && result.success) {
                const refreshed = result.odontogram_data;
                this.state.teeth = refreshed.teeth || {};
                this.state.stats = refreshed.stats || {};
                this.state.diagnosisMasters = refreshed.diagnosis_masters || this.state.diagnosisMasters;

                this.updateAllToothMaterials();

                this.notification.add(
                    _t("Tooth %s condition successfully recorded!", this.state.selectedTooth),
                    { type: "success" }
                );

                // Switch to history tab to show the recorded finding
                this.state.activePanelTab = "history";
            }
        } catch (error) {
            console.error("Failed to save tooth finding:", error);
            this.notification.add(error.message || _t("Failed to save tooth finding."), {
                type: "danger",
            });
        } finally {
            this.state.isSaving = false;
        }
    }

    async onClearFinding() {
        if (!this.state.selectedTooth) return;
        const caseId = this.caseId || this.getCaseId();
        if (!caseId) {
            this.notification.add(_t("Please save the dental case before clearing findings."), {
                type: "warning",
            });
            return;
        }

        this.state.isSaving = true;

        try {
            const result = await this.orm.call("dental.case", "clear_tooth_finding", [caseId], {
                tooth_number: this.state.selectedTooth,
            });

            if (result && result.success) {
                const refreshed = result.odontogram_data;
                this.state.teeth = refreshed.teeth || {};
                this.state.stats = refreshed.stats || {};
                this.state.diagnosisMasters = refreshed.diagnosis_masters || this.state.diagnosisMasters;

                this.updateAllToothMaterials();

                this.notification.add(
                    _t("Tooth %s marked as sound / cleared!", this.state.selectedTooth),
                    { type: "success" }
                );

                this.state.activePanelTab = "history";
            }
        } catch (error) {
            console.error("Failed to clear tooth finding:", error);
            this.notification.add(error.message || _t("Failed to clear tooth finding."), {
                type: "danger",
            });
        } finally {
            this.state.isSaving = false;
        }
    }

    // -------------------------------------------------------------------------
    // Cleanup
    // -------------------------------------------------------------------------

    cleanup3D() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        if (this.tabMutationObserver) {
            this.tabMutationObserver.disconnect();
        }
        if (this.onWindowResizeBound) {
            window.removeEventListener("resize", this.onWindowResizeBound);
        }
        if (this.controls) {
            this.controls.dispose();
        }
        if (this.renderer) {
            this.renderer.dispose();
        }
        this.is3DReady = false;
    }
}

export const dentalOdontogram3DField = {
    component: DentalOdontogram3DField,
    displayName: _t("Interactive 3D Odontogram"),
    supportedTypes: ["text", "char"],
};

registry.category("fields").add("dental_odontogram_3d", dentalOdontogram3DField);
