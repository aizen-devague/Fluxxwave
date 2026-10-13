# Fluxxwave
# FLUXXWAVE
## An Integrated Solar-Assisted Electric Vehicle Concept with Regenerative Energy Recovery and Intelligent Dual-Battery Management

**Project Domain:** Electric Mobility · Renewable Energy · Energy Systems Engineering · Embedded Systems · Intelligent Control

**Project Type:** Student-Led Engineering and Innovation Project

**Project Stage:** Conceptual Design and System Development

**Primary Objective:** To investigate the integration of supplementary solar energy generation, regenerative braking, dual-battery power management, and intelligent energy monitoring within a unified electric vehicle architecture.

---

## 1. Abstract

The electrification of transportation represents a significant technological transition in the pursuit of energy-efficient mobility, reduced dependence on petroleum-derived fuels, and the decarbonization of road transport. However, the practical performance of electric vehicles remains closely associated with the availability of charging infrastructure, the efficiency of electrical energy conversion, the characteristics of electrochemical energy storage, vehicle operating conditions, and the management of energy throughout the propulsion system.

**Fluxxwave** is a proposed hybrid-energy electric vehicle concept that explores the integration of three complementary engineering approaches: photovoltaic energy generation, regenerative energy recovery, and intelligent dual-battery management.

The central premise of Fluxxwave is that an electric vehicle's energy system should not be treated merely as a battery connected to an electric motor. Instead, it can be investigated as a coordinated network of energy sources, conversion mechanisms, storage elements, control systems, and electrical loads. Within this framework, supplementary solar generation may contribute energy during suitable illumination conditions, regenerative braking may recover a portion of the vehicle's kinetic energy that would otherwise be dissipated during deceleration, and an intelligent battery-management strategy may coordinate the operation of two energy-storage units according to their state of charge, health, temperature, and operational availability.

The proposed photovoltaic subsystem places solar panels on the vehicle's roof and bonnet, subject to practical considerations involving available surface area, panel orientation, shading, temperature, aerodynamic characteristics, and electrical conversion efficiency. The regenerative-energy subsystem investigates the recovery of braking energy through an appropriately designed motor-generator and power-electronic system. The battery-management subsystem introduces a proposed switching strategy in which the active battery approaches a configurable state-of-charge threshold of 20%, after which the controller may transfer the electrical load to a second battery, provided that the receiving battery and switching system satisfy all necessary safety conditions.

These mechanisms operate according to different physical principles. Photovoltaic generation converts incident solar radiation into electrical energy. Regenerative braking converts a portion of the vehicle's mechanical energy into electrical energy during deceleration. Battery management, by contrast, does not generate energy; it governs the allocation and availability of stored electrical energy.

Fluxxwave seeks to bring these functions together within a modular architecture that can be studied through engineering calculations, circuit design, embedded control, simulation, and eventually controlled experimental testing.

The project does not assume that integrating multiple energy-related technologies automatically improves overall efficiency. Instead, its central research question is whether coordinated energy management can improve useful energy utilization under clearly defined operating conditions without introducing disproportionate conversion losses, system complexity, cost, or safety risks.

The proposed system therefore provides a framework for investigating the relationship between energy harvesting, energy storage, power conversion, control logic, and real-world vehicle performance.

**Keywords:** Electric vehicles, photovoltaic energy, regenerative braking, kinetic energy recovery, dual-battery architecture, battery management systems, energy optimization, embedded control, sustainable mobility.

---

## 2. Introduction and Motivation

### 2.1 The energy challenge in electric mobility

Electric vehicles replace conventional internal-combustion propulsion with electrically driven powertrains. This transition changes the way energy is stored, converted, distributed, and consumed within a vehicle.

In a conventional electric vehicle, electrical energy is stored in a traction battery and supplied to an electric motor through power-electronic equipment. The motor converts electrical energy into mechanical work, which is transmitted to the wheels to produce motion.

Although electric drivetrains can be highly efficient, the vehicle still operates within a physical energy system governed by conservation of energy and thermodynamic constraints.

Energy is consumed by propulsion, aerodynamic resistance, tire deformation, auxiliary electrical equipment, thermal-management systems, and other operating requirements. Additional energy losses occur during battery charging and discharging, electrical conversion, motor operation, and mechanical transmission.

Consequently, an electric vehicle's effective range depends on more than the nominal capacity of its battery. It also depends on how efficiently energy is converted, how much energy can be recovered, how the vehicle is operated, and how intelligently the available energy is managed.

Fluxxwave approaches this problem by examining several complementary opportunities for improving the utilization of electrical energy.

### 2.2 The rationale for a multi-source energy architecture

The proposed Fluxxwave architecture considers three principal functions:

1. **Supplementary energy generation:** Photovoltaic panels can convert sunlight into electrical energy that may be used by the vehicle's electrical system or stored in a compatible battery.
2. **Energy recovery:** Regenerative braking can recover part of the vehicle's kinetic energy during deceleration when the motor, inverter, battery, and operating conditions permit it.
3. **Energy coordination:** A dual-battery controller can manage which battery supplies the electrical load, subject to appropriate electrical, thermal, and state-of-charge constraints.

These functions address different parts of the energy-management problem. Solar panels introduce an external energy source, regenerative braking reduces some otherwise avoidable energy dissipation, and battery management governs the distribution of stored energy.

Their integration must therefore be evaluated as a system rather than as three independent features.

### 2.3 The motivation behind Fluxxwave

Fluxxwave originates from the idea that sustainable vehicle engineering should investigate not only how energy is consumed, but also how supplementary energy can be collected, how otherwise recoverable energy can be retained, and how stored energy can be distributed more effectively.

The project aims to translate this idea into a structured engineering investigation.

Rather than presenting an unverified vehicle concept as a completed technological breakthrough, Fluxxwave is intended to develop through progressively more rigorous stages: theoretical analysis, mathematical modelling, system simulation, low-voltage experimentation, subsystem integration, and performance evaluation.

This development philosophy allows the project to distinguish between what is physically possible, what is technically feasible, what is economically practical, and what has actually been demonstrated.

---

## 3. Vision and Mission

### Vision

To investigate and develop an integrated electric mobility architecture that combines supplementary renewable energy generation, recoverable mechanical energy, intelligent electrical energy management, and measurable engineering performance.

### Mission

To design, model, evaluate, and progressively validate an electric vehicle energy-management concept through the integration of photovoltaic generation, regenerative braking, dual-battery coordination, embedded monitoring, and data-driven analysis.

### Core objectives

The principal objectives of Fluxxwave are:

- Investigate the practical contribution of vehicle-mounted photovoltaic panels to electrical energy availability.
- Examine the feasibility and limitations of regenerative braking as a method of recovering a portion of vehicle kinetic energy.
- Develop a dual-battery management strategy based on configurable state-of-charge thresholds and battery operating constraints.
- Explore the use of embedded controllers and monitoring software for coordinating energy-related subsystems.
- Establish a mathematical framework for analysing energy flows, conversion losses, and system-level performance.
- Develop reproducible simulations and experiments that distinguish theoretical expectations from measured outcomes.
- Identify engineering, economic, environmental, and safety constraints that influence practical implementation.

---

## 4. Conceptual System Architecture

Fluxxwave is organised around an energy-flow architecture consisting of generation, recovery, conversion, storage, distribution, propulsion, sensing, and supervisory control.

### 4.1 Principal subsystems

| Subsystem | Primary function | Proposed implementation |
|---|---|---|
| Photovoltaic subsystem | Converts solar radiation into electrical energy | Roof- and bonnet-mounted solar panels |
| Solar power conditioning | Regulates photovoltaic electrical output | Suitable DC-DC converter or solar charge controller |
| Regenerative-energy subsystem | Recovers a portion of kinetic energy during deceleration | Compatible motor-generator and bidirectional power electronics |
| Battery subsystem A | Supplies electrical energy to the system | Protected battery pack with suitable monitoring |
| Battery subsystem B | Provides an alternative energy-storage source | Independently monitored battery pack |
| Battery-management system | Monitors battery operating conditions and enforces protection limits | Appropriate BMS and battery telemetry |
| Switching subsystem | Coordinates the transfer of the permitted electrical load between batteries | Interlocked switching arrangement or controlled power electronics |
| Embedded controller | Executes supervisory control logic | Microcontroller-based control system |
| Monitoring interface | Displays energy and battery information | Computer, dashboard, or local visual interface |
| Propulsion subsystem | Converts electrical energy into mechanical motion | Compatible motor controller and electric motor |

The table describes the proposed functional architecture. The actual hardware configuration will depend on the selected battery chemistry, voltage, current requirements, motor topology, and development stage.

### 4.2 Functional energy flow

At the conceptual level, the system can be represented as follows:

```text
                     SOLAR RADIATION
                            |
                            v
                    PHOTOVOLTAIC PANELS
                            |
                            v
                   SOLAR POWER CONDITIONING
                            |
                            v
                      DC ENERGY BUS
                            |
             +--------------+--------------+
             |                             |
             v                             v
        BATTERY A                      BATTERY B
             |                             |
             +--------------+--------------+
                            |
                            v
                  BATTERY SELECTION AND
                    POWER MANAGEMENT
                            |
                            v
                   MOTOR CONTROLLER
                            |
                            v
                      ELECTRIC MOTOR
                            |
                            v
                       VEHICLE MOTION
                            |
                            v
                  DECELERATION / BRAKING
                            |
                            v
                  REGENERATIVE OPERATION
                            |
                            v
                 ELECTRICAL ENERGY RETURN
                            |
                            v
                COMPATIBLE STORAGE SYSTEM
```

This is a conceptual energy-flow diagram, not a finalized electrical schematic. The precise arrangement of the solar subsystem, batteries, inverter, motor, and regenerative charging path must be determined from the electrical architecture selected for implementation.

In particular, the regenerative path must be compatible with the motor drive and battery-charging limits. A separate generator connected mechanically to a continuously driven wheel should not be assumed to provide free energy: extracting electrical power from a moving vehicle introduces a corresponding mechanical load.

### 4.3 Supervisory control

A supervisory controller may coordinate information from the battery-management systems, solar power-conditioning equipment, motor controller, and vehicle sensors.

Its responsibilities could include:

- Monitoring battery state of charge and permitted operating conditions.
- Determining whether a battery is eligible to supply the load.
- Applying the configurable battery-selection threshold.
- Preventing incompatible or unsafe switching operations.
- Monitoring solar power availability.
- Recording regenerative-energy estimates or measurements.
- Displaying system status and fault information.
- Logging data for later analysis.

The supervisory controller must not replace dedicated battery protection circuitry, electrical interlocks, or other safety-critical functions.

---

## 5. Photovoltaic Energy Generation

### 5.1 Operating principle

Photovoltaic cells convert a portion of incident solar radiation into electrical energy through semiconductor processes.

When light is absorbed by a photovoltaic material, it can generate charge carriers that contribute to electrical current under suitable electrical conditions. Multiple cells are interconnected to form modules capable of supplying useful voltage and current.

For Fluxxwave, photovoltaic modules are proposed for installation on the roof and bonnet, subject to packaging and vehicle-design constraints.

The intended role of the photovoltaic subsystem is supplementary energy generation. It is not assumed that the available vehicle surface area will be sufficient to power the entire traction system under all operating conditions.

### 5.2 Theoretical power estimation

A simplified estimate of photovoltaic output is:

\[
P_{\mathrm{PV}} = G A \eta_{\mathrm{PV}}
\]

where:

- \(P_{\mathrm{PV}}\) is the estimated electrical output in watts.
- \(G\) is incident solar irradiance in watts per square metre.
- \(A\) is the effective illuminated photovoltaic area in square metres.
- \(\eta_{\mathrm{PV}}\) is the conversion efficiency expressed as a fraction.

For example, suppose a hypothetical installation has an effective panel area of \(2.0\,\mathrm{m^2}\), receives irradiance of \(800\,\mathrm{W/m^2}\), and has a conversion efficiency of \(22\%\).

The idealised estimate is:

\[
P_{\mathrm{PV}}
=800\times2.0\times0.22
=352\,\mathrm{W}
\]

This represents an illustrative estimate under the stated assumptions, not a measured Fluxxwave specification.

Actual output will differ because of cell temperature, partial shading, orientation, surface contamination, wiring losses, power-conditioning efficiency, and variations in irradiance.

### 5.3 Daily energy contribution

The approximate energy generated over a period can be calculated as:

\[
E_{\mathrm{PV}} = \int_{t_0}^{t_1} P_{\mathrm{PV}}(t)\,dt
\]

If power is expressed in kilowatts and time in hours, the resulting energy is measured in kilowatt-hours.

For preliminary estimates, a simplified expression is:

\[
E_{\mathrm{PV}}
\approx P_{\mathrm{rated}} H_{\mathrm{eq}} f_{\mathrm{sys}}
\]

where:

- \(P_{\mathrm{rated}}\) is the installed photovoltaic capacity in kilowatts.
- \(H_{\mathrm{eq}}\) is the equivalent full-power solar duration in hours.
- \(f_{\mathrm{sys}}\) is an aggregate factor accounting for relevant real-world losses.

The equivalent full-power duration must be estimated from the intended location, season, parking conditions, and installation geometry rather than assumed to be equal to the number of daylight hours.

### 5.4 Engineering constraints

The design must consider:

- Limited installation area on the roof and bonnet.
- Changes in irradiance during the day.
- Shading from buildings, trees, and nearby vehicles.
- Cell temperature and its influence on electrical output.
- Mechanical durability and weather protection.
- Aerodynamic and aesthetic constraints.
- Electrical isolation and compatibility with the charging system.
- Additional mass and its effect on energy consumption.
- Safe integration with the vehicle's electrical architecture.

### 5.5 Proposed development

The photovoltaic subsystem can initially be investigated using a small panel, an appropriate charge controller, and a monitored low-voltage storage system.

Measurements should include panel voltage, current, estimated power, illumination conditions, and accumulated energy where appropriate.

The results can then be compared with theoretical estimates to assess conversion losses and the usefulness of solar generation under the selected conditions.

---

## 6. Regenerative Braking and Kinetic Energy Recovery

### 6.1 The physical principle

A moving vehicle possesses kinetic energy. During deceleration, this energy must be transferred or dissipated through the vehicle's braking and drivetrain systems.

In conventional friction braking, much of the relevant mechanical energy is dissipated as heat. In a compatible electric drivetrain, the traction motor may operate as a generator during deceleration, converting part of the vehicle's mechanical energy into electrical energy.

This process is known as regenerative braking.

Fluxxwave proposes investigating regenerative energy recovery as a method of reducing some otherwise avoidable energy losses during suitable driving conditions.

### 6.2 Kinetic energy

The translational kinetic energy of a vehicle can be approximated by:

\[
E_k = \frac{1}{2}mv^2
\]

where:

- \(E_k\) is kinetic energy in joules.
- \(m\) is the effective vehicle mass in kilograms.
- \(v\) is vehicle speed in metres per second.

Consider a hypothetical vehicle with a mass of \(1{,}200\,\mathrm{kg}\) travelling at \(15\,\mathrm{m/s}\).

Its translational kinetic energy is:

\[
E_k = \frac{1}{2}(1200)(15)^2
\]

\[
E_k = 135{,}000\,\mathrm{J}
\]

Since one kilowatt-hour is equal to \(3.6\times10^6\) joules:

\[
E_k = 0.0375\,\mathrm{kWh}
\]

This value represents the vehicle's translational kinetic energy at the specified speed. It is not the amount of electricity that can necessarily be recovered during braking.

The recoverable amount is smaller because of drivetrain losses, motor and inverter efficiency, battery charging constraints, tire and road effects, and the fraction of braking force that must be supplied through other means.

### 6.3 Estimating recoverable energy

A simplified estimate is:

\[
E_{\mathrm{rec}} \approx \eta_{\mathrm{rec}} \Delta E_k
\]

where:

- \(E_{\mathrm{rec}}\) is recovered electrical energy.
- \(\eta_{\mathrm{rec}}\) is an aggregate recovery efficiency.
- \(\Delta E_k\) is the reduction in kinetic energy during deceleration.

The aggregate efficiency must be established through suitable measurements or justified assumptions. It should not be treated as a universal constant.

The total kinetic energy available for recovery may also include rotational energy from the wheels and other rotating components, depending on the accuracy required by the model.

### 6.4 Why continuous wheel-driven generation is different

Fluxxwave's original energy-recovery concept focuses on energy associated with wheel motion. Its engineering development must distinguish between two substantially different approaches.

**Regenerative braking:** The electric drivetrain recovers part of the vehicle's kinetic energy during deceleration. This can improve energy utilization because some energy that would otherwise be dissipated as heat is returned to the electrical system.

**Continuous generation from driven wheels:** A generator that extracts energy from wheels during powered cruising imposes a mechanical load. The propulsion system must supply additional energy to overcome that load, including conversion losses. It does not provide an independent source of energy and should not be assumed to increase net range.

For this reason, regenerative braking is the physically grounded starting point for investigating kinetic energy recovery in Fluxxwave.

### 6.5 Conditions affecting regeneration

Regenerative operation depends on:

- Vehicle speed and deceleration.
- Motor and inverter operating limits.
- Battery state of charge.
- Battery temperature and permitted charging current.
- Available traction and road conditions.
- Required braking force.
- Power-electronic efficiency.
- The compatibility of the selected drivetrain.

Regenerative braking cannot always provide all required braking force. A practical vehicle must retain an appropriate friction-braking system and use a properly engineered braking controller.

### 6.6 Proposed experimental investigation

A preliminary investigation can use a compatible low-voltage motor-generator demonstration, appropriate power electronics, and a protected storage system.

The experiment should compare mechanical input, electrical output, and conversion losses under controlled conditions.

For a vehicle-level investigation, recovered energy should be measured or estimated over a defined driving cycle and compared with total traction energy consumption.

---

## 7. Dual-Battery Architecture

### 7.1 Motivation

Battery storage is central to an electric vehicle's operation. However, using two batteries does not automatically double efficiency, range, or available energy relative to an otherwise equivalent system.

The potential value of a dual-battery arrangement depends on the purpose of the second battery and the strategy used to coordinate the two storage units.

Fluxxwave proposes a dual-battery architecture in which one battery supplies the permitted electrical load while another remains available as an alternative source, subject to its own operating conditions.

The arrangement is intended to provide a platform for investigating load transfer, energy availability, battery-state monitoring, and supervisory control.

### 7.2 Proposed operating principle

The initial control concept uses a configurable state-of-charge threshold of 20%.

Under normal conditions, the controller monitors the active battery and evaluates whether it remains eligible to supply the load.

When the active battery approaches the defined threshold, the controller may initiate a transfer to the second battery if the receiving battery has sufficient available charge and satisfies all relevant safety and electrical constraints.

The threshold is a proposed control parameter, not a universal optimum for lithium-ion or other battery chemistries.

A real implementation must also consider the battery manufacturer's permitted discharge limits, the BMS's operating restrictions, voltage sag under load, temperature, state of health, and the characteristics of the switching hardware.

### 7.3 Conceptual state machine

The battery-selection logic can be expressed as a state machine:

```text
                SYSTEM INITIALIZATION
                         |
                         v
                READ BATTERY STATUS
                         |
                         v
               CHECK SYSTEM ELIGIBILITY
                         |
                         v
                SELECT ACTIVE BATTERY
                         |
                         v
                MONITOR STATE OF CHARGE
                         |
                         v
              IS ACTIVE BATTERY NEAR
                  THE SET THRESHOLD?
                    /          \
                  NO            YES
                  |              |
                  |              v
                  |       CHECK ALTERNATE
                  |          BATTERY
                  |              |
                  |              v
                  |       IS IT AVAILABLE
                  |        AND SAFE TO USE?
                  |          /        \
                  |        YES         NO
                  |         |           |
                  |         v           v
                  |     CONTROLLED   ENTER SAFE
                  |      TRANSFER    RESPONSE
                  |         |
                  |         v
                  |     VERIFY NEW
                  |     ACTIVE STATE
                  |         |
                  +---------+
```

This diagram describes the intended decision process. It does not specify a complete safety-certified switching circuit.

### 7.4 Why state of charge matters

State of charge (SoC) estimates the amount of charge remaining relative to a battery's usable capacity under defined conditions.

It is commonly expressed as a percentage:

\[
\mathrm{SoC}(\%) =
\frac{Q_{\mathrm{remaining}}}
{Q_{\mathrm{usable}}}
\times 100
\]

where the quantities represent compatible estimates of remaining and usable charge.

In practice, estimating SoC can require current integration, voltage measurements, temperature compensation, battery-specific models, and information from the battery-management system.

Voltage alone may not provide an accurate state-of-charge estimate under all operating conditions.

### 7.5 Battery switching is not merely a relay operation

A safe transition between two energy-storage units requires more than detecting a threshold and activating a relay.

A practical design must consider:

- Compatibility of battery voltage and electrical architecture.
- Permitted charge and discharge currents.
- Independent battery protection.
- Prevention of unintended battery-to-battery current flow.
- Switching-device current ratings and fault behaviour.
- Electrical transients during load transfer.
- Continuity of supply to critical electronics.
- Detection of a failed or unavailable receiving battery.
- Verification that the intended switching state was achieved.
- A defined response when neither battery is eligible.

Depending on the final topology, controlled power electronics or a properly engineered switching arrangement may be preferable to simple relay switching.

The exact solution must be established through circuit design, component selection, fault analysis, and testing.

### 7.6 Potential research questions

The dual-battery subsystem provides opportunities to investigate:

- How threshold selection affects usable energy and switching frequency.
- How different battery capacities influence load-sharing strategies.
- Whether hysteresis reduces unnecessary repeated switching.
- How temperature and state-of-health information should affect battery selection.
- How switching losses and standby consumption influence overall efficiency.
- How to handle faults without interrupting essential monitoring and protection functions.

---

## 8. Intelligent Energy Management

### 8.1 Purpose

The effectiveness of an integrated energy system depends on how its components are coordinated.

Fluxxwave therefore proposes a supervisory energy-management layer that combines information from energy generation, storage, propulsion, and system monitoring.

The initial implementation may use deterministic control logic. More advanced predictive or artificial-intelligence-based methods can be explored later if reliable data and a clearly defined optimisation objective become available.

### 8.2 Proposed monitoring variables

| Variable | Purpose |
|---|---|
| Battery SoC | Estimates remaining usable charge |
| Battery voltage | Supports electrical-state monitoring |
| Battery current | Supports power and energy calculations |
| Battery temperature | Helps determine safe operating eligibility |
| Solar voltage | Monitors photovoltaic electrical output |
| Solar current | Supports solar power estimation |
| Motor electrical power | Estimates traction-system demand |
| Regenerative power | Estimates electrical energy recovered during deceleration |
| Active battery identifier | Records the selected energy-storage unit |
| System fault status | Identifies unavailable or abnormal subsystems |

The available measurements depend on the hardware selected. A conceptual variable should not be represented as a measured quantity until an appropriate sensor, interface, or estimation method has been implemented.

### 8.3 Energy-management hierarchy

A possible control hierarchy contains three levels.

**Level 1: Protection**

Battery-management systems, electrical protection, motor-controller limits, and hardware interlocks enforce operating constraints.

**Level 2: Supervisory coordination**

The supervisory controller selects the eligible battery, monitors source availability, coordinates permitted energy flows, and records system status.

**Level 3: Optimisation and analytics**

A monitoring application analyses energy data, compares operating conditions, estimates performance, and may eventually evaluate predictive control strategies.

This separation helps prevent experimental optimisation software from replacing safety-critical hardware protection.

### 8.4 Future REMS concept

A future development direction is a proposed **REMS (Renewable Energy Management System)** for coordinating the vehicle's supplementary energy sources and storage subsystems.

REMS could eventually support:

- Solar-energy monitoring.
- Battery-state visualisation.
- Switching-event logging.
- Energy-flow analysis.
- Regenerative-energy accounting.
- Efficiency comparisons across test conditions.
- Forecasting of expected solar availability.
- Predictive maintenance research based on validated sensor data.

The term describes a proposed system architecture. Its advanced functions should be labelled as conceptual, simulated, or implemented according to their actual development status.

### 8.5 Why artificial intelligence is not the starting requirement

An intelligent system does not necessarily require machine learning.

For an early engineering prototype, deterministic control logic is often easier to test, interpret, and verify. A threshold-based controller provides a clear baseline against which more sophisticated strategies can be evaluated.

Machine learning or predictive optimisation becomes relevant when the project has sufficiently reliable data, a well-defined performance objective, suitable validation procedures, and evidence that a more complex method provides a meaningful advantage.

---

## 9. Mathematical Modelling and Energy Accounting

### 9.1 The conservation principle

Fluxxwave must be evaluated using an energy balance that distinguishes generated energy, recovered energy, stored energy, consumed energy, and conversion losses.

For a defined system boundary and time interval, a simplified balance can be written as:

\[
E_{\mathrm{in}} + E_{\mathrm{generated}}
=
E_{\mathrm{useful}} + E_{\mathrm{losses}}
+ \Delta E_{\mathrm{stored}}
\]

The terms must be defined consistently for the selected system boundary. Energy transferred between internal components should not be counted twice.

For example, solar energy entering the vehicle's electrical system is an external input, while energy transferred from a battery to a motor and subsequently recovered during braking is part of an internal energy cycle. Counting both the original battery discharge and the recovered energy as independent external energy sources would distort the energy balance.

### 9.2 Electrical power

For a DC circuit, instantaneous electrical power can be calculated as:

\[
P(t) = V(t)I(t)
\]

where \(V(t)\) is voltage and \(I(t)\) is current under the selected sign convention.

If voltage and current are approximately constant over a short interval:

\[
E \approx VIt
\]

where \(t\) is expressed in seconds when energy is required in joules.

When voltage or current varies substantially, energy should be calculated by integrating measured power:

\[
E = \int_{t_0}^{t_1} P(t)\,dt
\]

For discrete measurements, numerical integration methods can be used to estimate the accumulated energy.

### 9.3 Conversion efficiency

A subsystem's conversion efficiency can be defined as:

\[
\eta =
\frac{E_{\mathrm{useful,out}}}
{E_{\mathrm{in}}}
\times100\%
\]

The input and output quantities must correspond to the same conversion process and time interval.

For a complete vehicle-level system, the evaluation must include the effects of storage, conversion, and auxiliary loads rather than combining individual component efficiencies without accounting for the energy flows between them.

### 9.4 Net energy contribution

A useful research metric for supplementary solar generation is the net electrical energy delivered after relevant conversion losses:

\[
E_{\mathrm{solar,net}}
=
E_{\mathrm{solar,harvested}}
-
E_{\mathrm{solar,path\,losses}}
\]

For regenerative braking, the recovered energy must be evaluated in relation to the kinetic energy removed during deceleration and the additional losses associated with the recovery process.

The value of these contributions should ultimately be assessed against a defined baseline vehicle or baseline energy-management strategy.

### 9.5 Performance metrics

Potential metrics include:

- Solar energy generated per day.
- Regenerative electrical energy recovered per test cycle.
- Net electrical energy delivered to the traction system.
- Energy consumption per kilometre.
- Energy lost during power conversion.
- Frequency of battery switching.
- Time spent using each battery.
- Switching events successfully completed.
- System downtime caused by faults.
- Estimated cost per unit of useful energy.
- Mass and complexity introduced by additional hardware.

Not every metric will be available at the concept stage. Each should be introduced only when the necessary data and measurement method exist.

---

## 10. Proposed Experimental Methodology

Fluxxwave is intended to progress through a series of controlled development stages rather than moving directly from concept to a complete road vehicle.

### Stage 1: Literature review and requirements definition

Investigate photovoltaic systems, regenerative braking, battery-management systems, DC power conversion, and electric drivetrain architecture.

Define the intended system boundary, principal operating conditions, design constraints, and performance metrics.

**Deliverables:**
- Literature review.
- Preliminary requirements document.
- System block diagram.
- Initial risk assessment.

### Stage 2: Analytical modelling

Develop mathematical estimates for photovoltaic output, vehicle kinetic energy, potential regenerative recovery, and battery energy availability.

Identify the assumptions and uncertainties associated with each calculation.

**Deliverables:**
- Energy-flow calculations.
- Preliminary component requirements.
- Parameter and assumption register.
- Baseline performance model.

### Stage 3: Simulation

Create a software model of the dual-battery switching logic and energy-flow behaviour.

Simulate normal operation, threshold transitions, unavailable batteries, sensor errors, and other relevant cases.

**Deliverables:**
- Simulation code.
- State-transition diagrams.
- Test cases.
- Recorded simulation results.

### Stage 4: Low-voltage subsystem development

Develop suitable educational test setups for monitoring battery state, reading sensors, and demonstrating control logic.

Any battery-related experiment must use an appropriate protected system and components selected for the intended electrical conditions.

**Deliverables:**
- Sensor interface.
- Controller implementation.
- Battery-selection demonstration.
- Recorded low-voltage test data.

### Stage 5: Integrated energy demonstration

Integrate selected subsystems after verifying their individual operation.

Demonstrate the photovoltaic measurement path, battery-management logic, and a compatible regenerative-energy recovery setup where suitable equipment is available.

**Deliverables:**
- Integrated demonstration.
- System architecture documentation.
- Measured energy-flow data.
- Fault-handling test results.

### Stage 6: Performance evaluation

Compare measured performance with the original model and baseline assumptions.

Analyse discrepancies, repeat measurements where necessary, and document the limits of the experimental setup.

**Deliverables:**
- Performance report.
- Energy-balance analysis.
- Limitations and uncertainty discussion.
- Revised design recommendations.

---

## 11. Simulation Strategy

Simulation can help evaluate control logic and identify design problems before physical integration.

A software-only model is particularly useful for a student project because it can be developed incrementally without immediately requiring a complete vehicle prototype.

### 11.1 Initial simulation objectives

The first simulation should focus on the dual-battery management system.

It can model:

- Two batteries with independently configurable initial states of charge.
- A simulated electrical load.
- A configurable switching threshold.
- Battery eligibility checks.
- A simplified energy-consumption model.
- Switching-event logging.
- Detection of unavailable batteries.
- Graphs showing state of charge over time.

The initial model should be clearly labelled as a simulation. Its results will depend on the assumptions and equations used.

### 11.2 Possible software tools

- **Python:** Numerical modelling, simulation, data analysis, and visualisation.
- **Matplotlib:** Plotting battery state of charge, power, and energy over time.
- **NumPy:** Numerical calculations and array operations.
- **Pandas:** Organising and analysing recorded data.
- **Arduino-compatible development tools:** Embedded control experiments, where suitable hardware is available.
- **Git and GitHub:** Version control, documentation, and collaboration.

These tools are proposed options rather than a declaration that every subsystem has already been implemented.

### 11.3 Baseline comparison

A useful simulation should compare the proposed strategy against a defined baseline.

For example, a dual-battery controller could be evaluated against a simpler strategy using the same assumed battery capacities, load profile, and initial stored energy.

This comparison would help determine whether the added switching logic offers a measurable benefit in energy availability, system continuity, or another clearly specified metric.

The result should not be interpreted as proof of improved vehicle range unless the model includes the relevant vehicle-level energy flows and is validated against appropriate measurements.

---

## 12. Safety and Engineering Constraints

Safety is a fundamental design requirement, particularly when the project involves rechargeable batteries, high-current electrical paths, motor controllers, and moving mechanical components.

Fluxxwave's development should proceed through low-risk, controlled demonstrations before any attempt to integrate a vehicle-scale system.

### 12.1 Electrical safety

The electrical design must account for:

- Correct voltage and current ratings.
- Short-circuit protection.
- Overcurrent and overvoltage protection.
- Appropriate wiring and connector ratings.
- Electrical isolation where required.
- Safe charging and discharging limits.
- Prevention of unintended current paths between batteries.
- Suitable enclosures and environmental protection.
- Emergency disconnection provisions appropriate to the test setup.

### 12.2 Battery safety

The battery subsystem should use appropriate battery-management and protection equipment.

The design must consider overcharge, excessive discharge, overheating, short circuits, cell imbalance, and battery faults. The specific protections required depend on the battery chemistry and configuration.

A software threshold of 20% must not replace the manufacturer's required operating limits or the battery-management system's protection functions.

### 12.3 Mechanical and braking safety

Regenerative braking must be developed within a compatible drivetrain architecture.

Any physical demonstration should be designed so that rotating parts, electrical connections, and stored energy are appropriately controlled and protected.

A student prototype should not be treated as roadworthy merely because its electrical components operate correctly. A complete vehicle would require professional engineering, suitable mechanical and braking systems, and compliance with applicable safety requirements.

### 12.4 Software safety

The control system should define its behaviour when:

- A sensor produces invalid readings.
- A battery becomes unavailable.
- Switching is unsuccessful.
- Communication with a monitoring device is interrupted.
- Measured conditions exceed permitted limits.
- The controller restarts unexpectedly.

The system should default to a defined safe response rather than assume that every operation succeeds.

---

## 13. Environmental and Sustainability Considerations

Fluxxwave is motivated by sustainable mobility, but environmental benefit must be evaluated across the relevant lifecycle rather than inferred from the presence of solar panels or batteries alone.

### 13.1 Potential benefits

The proposed architecture may offer several benefits under suitable conditions:

- Supplementary solar electricity can reduce the amount of energy drawn from an external charging source.
- Regenerative braking can reduce some otherwise dissipated kinetic energy.
- Energy monitoring can identify inefficient operating conditions.
- Improved energy accounting can support better design decisions.
- Modular development can help compare alternative technologies before larger investments are made.

### 13.2 Limitations and trade-offs

Additional photovoltaic modules, converters, wiring, controllers, and battery hardware may introduce cost, mass, material demand, and conversion losses.

The net benefit depends on the amount of useful energy supplied or recovered relative to the additional energy consumption, cost, mass, and complexity of the installed equipment.

Environmental assessment should also consider electricity generation, battery manufacture, component lifetime, repairability, and end-of-life treatment where sufficient information is available.

### 13.3 Evidence-based sustainability

Fluxxwave will treat environmental benefit as a research question.

Claims about reduced emissions, extended driving range, improved efficiency, or reduced charging requirements should be supported by a defined comparison and appropriate data.

The objective is not merely to add renewable-energy components to a vehicle, but to investigate whether the resulting system offers a measurable advantage under realistic conditions.

---

## 14. Research Questions and Hypotheses

The project can be developed around the following research questions.

### Research Question 1: Photovoltaic contribution

How does vehicle-mounted photovoltaic generation contribute to the electrical energy available to a vehicle under different illumination conditions?

**Hypothesis:** Photovoltaic generation can provide a measurable supplementary energy contribution when sufficient irradiance and suitable electrical operating conditions are available.

**Evaluation:** Compare measured photovoltaic energy output with theoretical estimates and, where relevant, the vehicle's electrical energy consumption.

### Research Question 2: Regenerative energy recovery

How much electrical energy can be recovered during controlled deceleration using a compatible regenerative system?

**Hypothesis:** A suitable regenerative drivetrain can recover a portion of the kinetic energy removed during deceleration.

**Evaluation:** Measure or estimate mechanical energy removed and electrical energy returned to storage, accounting for the limitations of the test setup.

### Research Question 3: Dual-battery control

How does a threshold-based battery-selection strategy affect switching behaviour, usable energy, and system continuity?

**Hypothesis:** A properly designed selection strategy can coordinate the use of two eligible energy-storage units, although the value of the strategy depends on the architecture and operating conditions.

**Evaluation:** Simulate defined load profiles and record switching events, battery-state trajectories, and fault-handling behaviour.

### Research Question 4: Integrated energy management

Can a coordinated energy-management architecture provide a measurable advantage over an equivalent baseline system?

**Hypothesis:** The result will depend on the combined effects of energy availability, conversion efficiency, control strategy, component mass, and system losses.

**Evaluation:** Compare equivalent operating scenarios using a consistent energy boundary and explicitly stated assumptions.

These hypotheses are intended to be tested, not presented as established findings.

---

## 15. Limitations of the Current Concept

Several limitations must be acknowledged during development.

**Limited photovoltaic area:** The available roof and bonnet surfaces constrain installed photovoltaic capacity. Actual output varies with illumination, shading, orientation, temperature, and conversion losses.

**Intermittent solar availability:** Solar generation depends on environmental conditions and cannot be treated as a constant power source.

**Limited regenerative opportunity:** Regenerative braking can recover only a portion of the energy available during suitable deceleration events. It does not continuously generate net energy during powered cruising.

**Battery-management complexity:** Dual-battery operation introduces additional monitoring, switching, protection, and integration requirements.

**Uncertain system-level benefit:** The combined effect of the proposed technologies must be established through modelling and testing. Adding components does not necessarily improve net performance.

**Prototype limitations:** Results obtained from a low-voltage demonstration or software simulation may not translate directly to a full-size vehicle.

**Dependence on assumptions:** Preliminary calculations may be sensitive to assumed panel area, irradiance, battery capacity, conversion efficiency, vehicle mass, and operating conditions.

**Cost and maintainability:** Additional components may increase the initial cost, installation complexity, and maintenance requirements.

Documenting these limitations is an essential part of engineering rather than a weakness in the project.

---

## 16. Development Roadmap

Fluxxwave is intended to develop incrementally.

| Phase | Focus | Expected outcome |
|---|---|---|
| Phase 1 | Requirements and literature review | Documented concept and system architecture |
| Phase 2 | Mathematical modelling | Initial energy estimates and assumptions |
| Phase 3 | Software simulation | Testable battery-management logic |
| Phase 4 | Sensor and controller development | Low-voltage monitoring demonstration |
| Phase 5 | Photovoltaic subsystem testing | Measured solar output under defined conditions |
| Phase 6 | Regenerative-energy demonstration | Controlled recovery measurements |
| Phase 7 | Subsystem integration | Coordinated prototype demonstration |
| Phase 8 | Performance evaluation | Comparison against a defined baseline |
| Phase 9 | Refinement and reporting | Revised design and reproducible technical documentation |

The phases may overlap, and their duration will depend on equipment availability, technical complexity, and the project's development resources.

### Proposed future directions

After the initial system has been demonstrated, possible extensions include:

- A live energy-monitoring dashboard.
- Data logging for battery state, solar output, and power consumption.
- More sophisticated battery-selection strategies.
- Predictive solar-generation estimates.
- Comparative evaluation of different switching thresholds.
- Model-based range estimation.
- Fault-detection research.
- Energy-aware route analysis.
- Simulation of alternative storage architectures.
- A documented lifecycle and cost assessment.

Advanced features should be introduced only when the underlying system and measurement methods are sufficiently developed.

---

## 17. Project Documentation and Reproducibility

Engineering results are more useful when other people can understand how they were obtained.

Fluxxwave therefore aims to document the assumptions, methods, software, test conditions, and limitations associated with its development.

Where appropriate, the repository should contain:

- System architecture diagrams.
- Circuit diagrams and component specifications.
- Mathematical calculations.
- Source code and dependency information.
- Simulation assumptions.
- Test procedures.
- Raw or appropriately processed experimental data.
- Graphs and performance summaries.
- Known limitations and unresolved issues.
- A record of changes to the design.

Each reported result should identify whether it is theoretical, simulated, estimated, or experimentally measured.

Experimental measurements should include enough information about the test conditions to permit meaningful interpretation and, where practical, reproduction.

This documentation approach supports technical review and helps prevent conceptual assumptions from being mistaken for validated engineering performance.

---

## 18. Suggested Repository Structure

As development progresses, the GitHub repository may use the following structure:

```text
Fluxxwave/
│
├── README.md
│
├── docs/
│   ├── project-overview.md
│   ├── system-architecture.md
│   ├── engineering-requirements.md
│   ├── energy-model.md
│   ├── safety-considerations.md
│   └── limitations.md
│
├── diagrams/
│   ├── system-block-diagram.png
│   ├── energy-flow-diagram.png
│   └── battery-state-machine.png
│
├── code/
│   ├── simulation/
│   ├── embedded/
│   └── analysis/
│
├── data/
│   └── README.md
│
├── results/
│   └── README.md
│
├── tests/
│   └── README.md
│
├── requirements.txt
│
└── LICENSE
```

This is a proposed organisational structure. Directories should be added as relevant work is created, rather than populated with empty files that imply nonexistent implementations.

Sensitive information, private credentials, and confidential data should not be committed to a public repository.

---

## 19. Contribution and Collaboration

Fluxxwave can support collaboration among students interested in electrical engineering, renewable energy, embedded systems, physics, programming, and sustainable mobility.

Potential areas of contribution include:

- Reviewing the energy model.
- Developing simulation code.
- Improving the documentation.
- Creating system diagrams.
- Evaluating control algorithms.
- Analysing experimental data.
- Identifying relevant technical literature.
- Reviewing engineering assumptions and limitations.

Contributions should be evaluated on technical clarity, correctness, reproducibility, and consistency with the documented project objectives.

Proposed changes should explain their purpose and, where applicable, include supporting calculations, tests, or references.

Collaboration should preserve a clear distinction between suggested improvements, implemented features, and experimentally verified results.

---

## 20. References and Further Reading

The following primary resources provide a starting point for understanding the engineering principles relevant to Fluxxwave.

1. **National Renewable Energy Laboratory (NREL)** — Research on photovoltaic technologies, solar resource assessment, renewable energy, and transportation energy systems.  
   https://www.nrel.gov/

2. **U.S. Department of Energy, Alternative Fuels Data Center** — Technical information on electric vehicles, regenerative braking, batteries, and vehicle energy use.  
   https://afdc.energy.gov/

3. **U.S. Department of Energy, Vehicle Technologies Office** — Research on advanced batteries, electric-drive systems, and vehicle efficiency.  
   https://www.energy.gov/eere/vehicles/vehicle-technologies-office

4. **IEEE Xplore** — Technical literature on power electronics, battery management, photovoltaic systems, motor drives, and embedded control.  
   https://ieeexplore.ieee.org/

5. **International Energy Agency (IEA)** — Research and reports on electric mobility, energy transitions, and transportation decarbonisation.  
   https://www.iea.org/

6. **NIST** — Measurement science, uncertainty, and standards-related resources relevant to experimental engineering.  
   https://www.nist.gov/

7. **GitHub Docs** — Documentation for repository management, Markdown, version control workflows, and collaboration.  
   https://docs.github.com/

Specific technical claims and design decisions should be supported by relevant publications, standards, manufacturer documentation, or reproducible measurements as the project develops. The resources above are starting points rather than citations for every claim in this document.

---

## 21. Conclusion

Fluxxwave presents a framework for investigating the coordination of photovoltaic generation, regenerative energy recovery, and dual-battery management within an electric vehicle energy system.

Its significance lies in treating energy generation, conversion, storage, and control as interdependent engineering functions rather than isolated technological additions.

The photovoltaic subsystem investigates the contribution of an external renewable energy source. The regenerative-energy subsystem examines the recovery of a portion of mechanical energy that would otherwise be dissipated during suitable deceleration. The dual-battery subsystem explores how stored energy can be made available through monitored and controlled selection, while the proposed supervisory architecture provides a means of observing and coordinating these functions.

The project's development depends on rigorous energy accounting, realistic component constraints, safe electrical integration, and systematic validation. In particular, solar generation must be assessed under realistic illumination conditions, regenerative recovery must be distinguished from energy extracted during powered cruising, and battery switching must be designed around appropriate protection and control requirements.

Fluxxwave is therefore not defined by the assumption that a particular combination of technologies will automatically produce superior vehicle performance. It is defined by the investigation of whether such a combination can deliver a measurable and practical benefit under specified conditions.

Through mathematical modelling, simulation, controlled experimentation, and transparent documentation, the project aims to evolve from an initial concept into an increasingly testable engineering system.

**The long-term objective is to develop an evidence-based approach to integrated electric vehicle energy management—one in which every proposed improvement is evaluated through physical principles, measurable performance, and clearly documented engineering decisions.**

---

## Project Status and Transparency

This repository documents the design and development of Fluxxwave as an evolving student innovation project.

Unless accompanied by implementation details and supporting evidence, the architecture, algorithms, performance improvements, and future capabilities described here should be understood as proposals or research objectives rather than completed or validated features.

As development progresses, the repository will distinguish between:

- **Proposed:** A design idea or intended capability.
- **Designed:** A documented architecture, circuit, or algorithm.
- **Simulated:** A model evaluated in software.
- **Implemented:** A feature developed in hardware or software.
- **Tested:** A feature evaluated under documented conditions.
- **Validated:** A result supported by appropriate evidence for its stated purpose.

This distinction is intended to make the project technically credible, scientifically transparent, and useful as a foundation for continued engineering work.
