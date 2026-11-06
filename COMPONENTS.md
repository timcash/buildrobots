# Robotics components and subcomponents

The **Building Robots in Utah** slide deck identifies five component families for a proposed manufacturing campus. This reference preserves the appendix’s 100 numbered entries and sourcing labels and explains what each entry does.

The first motion package combines a servomotor, precision gear reducer, and EtherCAT servo drive on one axis. The first optics applications use a machine-vision camera for inspection and an industrial fiber laser for welding.

## Counts by component family

| Component family | Appendix entries | L | U | E | Total |
| --- | --- | ---: | ---: | ---: | ---: |
| Servomotor | 01–20 | 8 | 11 | 1 | 20 |
| Precision gear reducer | 21–40 | 9 | 7 | 4 | 20 |
| EtherCAT servo drive | 41–60 | 6 | 14 | 0 | 20 |
| Industrial fiber laser | 61–80 | 7 | 7 | 6 | 20 |
| Machine-vision camera | 81–100 | 9 | 10 | 1 | 20 |
| **Total** | **01–100** | **39** | **49** | **12** | **100** |

- **L** · Utah fabrication or integration
- **U** · Qualify U.S. sources first
- **E** · Expand production with demand

The labels describe proposed sourcing actions. Verify supplier qualification and country of manufacture for the actual product. The count includes purchased parts, materials, assemblies, and software deliverables. Some entries describe items within other assemblies, and some are specific to alternative designs. Use the list for supply-chain screening and build a separate bill of materials for each product configuration.

## Servomotor

A brushless permanent-magnet servomotor converts controlled phase current into torque. The stator windings create a rotating magnetic field, the rotor turns the shaft, and the encoder returns shaft position to the drive. The reference design includes an encoder and an optional holding brake.

Early Utah work can include winding, impregnation, rotor assembly and balancing, shaft and housing machining, feedback alignment, and end-of-line testing. Verify torque, winding insulation, thermal performance, and feedback alignment against the buyer’s requirements.

### Electromagnetic assembly

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 01 | Stator lamination stack | Stacked electrical-steel laminations form the magnetic core and the slots for the windings. | L |
| 02 | Enamelled copper winding wire | Insulated copper conductor carries phase current through the stator coils. | U |
| 03 | Wound stator coils | Coils arranged by phase create the rotating magnetic field. | L |
| 04 | Slot liners and phase insulation | Dielectric layers isolate windings from the stator core and from other phases. | U |
| 05 | Slot wedges and lacing | Wedges and lacing hold the windings in place during operation. | U |
| 06 | Impregnation varnish or potting resin | Varnish or resin stabilizes the coils and supports insulation and heat transfer. | U |
| 07 | Rotor hub and back iron | The hub supports the rotor, and the back iron provides a magnetic return path. | L |
| 08 | Sintered NdFeB magnet segments | Permanent magnets supply the rotor field in the reference motor. | U |
| 09 | Magnet retention sleeve or banding | The sleeve or banding secures the magnets against centrifugal loads. | L |
| 10 | Motor temperature sensor | The sensor monitors temperature for protection or current derating. | U |

### Mechanical and feedback assembly

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 11 | Precision motor shaft | The shaft transmits rotor torque to the load or reducer. | L |
| 12 | Rotor support bearings | Bearings locate the rotor and support its radial and axial loads. | U |
| 13 | Motor housing and mounting flange | The housing protects the motor and conducts heat. The flange locates it on the machine. | L |
| 14 | Front and rear end bells | End bells close the motor and commonly locate the bearings. | L |
| 15 | Shaft seal | The seal limits ingress around the rotating shaft. | U |
| 16 | Absolute encoder module | The module reports absolute shaft angle for position feedback. | U |
| 17 | Encoder target or codewheel | The target is the scale or pattern read by the encoder in designs that use one. | E |
| 18 | Spring-applied holding brake | The spring applies the brake to hold a stationary shaft when brake power is removed. | U |
| 19 | Motor power and feedback connectors | Connectors provide separable interfaces for motor current and feedback signals. | U |
| 20 | Internal lead and feedback harness | The internal harness routes power, feedback, and sensor connections. | L |

[Deploy Robotic servomotor cutaway](https://deployrobotic.com/tour/#supply-servo-motor) · [Kollmorgen housed servo options](https://www.kollmorgen.com/en-us/developer-network/akm2g) · [Kollmorgen stator and rotor architecture](https://www.kollmorgen.com/en-us/products/motors/technologies-explained/what-is-a-frameless-motor)

## Precision gear reducer

A reducer trades speed for torque in a robot joint. The appendix covers two architectures. In a planetary reducer, planet gears mesh with a central sun and an internal ring. In a strain-wave reducer, an elliptical wave generator deforms the flexspline so it engages the rigid circular spline. The illustrated 200-tooth flexspline and 202-tooth circular spline yield a 100:1 reduction magnitude in the shown configuration.

Start with planetary gears and housings. Qualify heat treatment and gear grinding with suppliers as needed. Evaluate strain-wave flexsplines and bearings separately. Measure tooth geometry, backlash or lost motion, torsional stiffness, and endurance.

### Planetary gearset

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 21 | Sun gear | The center gear transmits input torque to the planet gears in a typical arrangement. | L |
| 22 | Planet gears | Planet gears mesh with the sun and ring and transmit load through the carrier. | L |
| 23 | Planetary ring gear | The internal-tooth ring surrounds the planet gears and provides their second mesh. | L |
| 24 | Planet carrier | The carrier holds the planet pins and commonly delivers the reduced-speed output. | L |
| 25 | Planet pins | Pins locate the planet gears and support their bearings. | L |
| 26 | Planet needle bearings | Needle bearings let the planet gears rotate on their pins in limited radial space. | U |
| 27 | Planet thrust washers | Washers locate the planets axially and provide a thrust surface. | U |
| 28 | Input shaft or pinion adapter | The shaft or adapter couples the motor to the reducer input. | L |
| 29 | Output shaft or flange | The output shaft or flange transmits torque to the joint or load. | L |
| 30 | Planetary gearbox housing | The housing supports the gearset and bearings and provides mounting interfaces. | L |

### Strain-wave and common parts

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 31 | Thin-wall flexspline cup | The thin toothed cup flexes with the wave generator and transfers reduced-speed motion. | E |
| 32 | Rigid circular spline | The rigid internal-tooth ring meshes with the flexspline. | E |
| 33 | Elliptical wave-generator cam | The elliptical cam imposes the deformation that moves the tooth engagement around the ring. | E |
| 34 | Flexible wave-generator bearing | The flexible bearing follows the elliptical cam while allowing relative rotation. | E |
| 35 | Crossed-roller output bearing | The output bearing supports radial, axial, and moment loads in a compact joint. | U |
| 36 | Bearing preload shims | Shims set axial clearances or bearing preload during assembly. | L |
| 37 | Rotary lip seal | The lip seal retains lubricant and limits contamination at a rotating interface. | U |
| 38 | Housing O-rings or gaskets | O-rings or gaskets seal stationary joints in the housing. | U |
| 39 | Low-backlash gear lubricant | Lubricant reduces friction and wear at gear teeth and bearings. | U |
| 40 | Gear steel or near-net blanks | Steel stock or near-net blanks supply material for cutting and finishing gears. | U |

[Deploy Robotic strain-wave reducer](https://deployrobotic.com/tour/#gears) · [Harmonic Drive operating principles](https://legacy.harmonicdrive.net/reference/operatingprinciples/) · [Neugart planetary reducers](https://www.neugart.com/en-us/planetary-gear-reducer)

## EtherCAT servo drive

The reference drive accepts motion commands over EtherCAT and closes current, speed, and position loops using motor feedback. A three-phase inverter switches a low-voltage DC supply to drive the motor. The reference architecture is DC-fed.

Prioritize PCB assembly, enclosure and thermal integration, and functional testing. Verify current sensing, encoder compatibility, thermal performance, EMC, EtherCAT interoperability, and the safety function where specified.

### Power stage and packaging

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 41 | Three-phase power MOSFETs | The inverter’s MOSFETs switch DC bus energy into controlled motor phase currents. | U |
| 42 | Gate-driver ICs | Gate drivers turn the power switches on and off using signals from the controller. | U |
| 43 | DC-link capacitors | Capacitors stabilize the DC bus and supply short switching-current pulses. | U |
| 44 | Phase-current shunts | Low-resistance shunts develop a voltage proportional to the measured current. | U |
| 45 | Current-sense amplifiers | Amplifiers condition the shunt signal for measurement by the controller. | U |
| 46 | DC-bus voltage sensing network | The sensing network scales bus voltage for monitoring and protection. | L |
| 47 | Input EMI filter components | Filter components limit conducted switching noise at the power input. | U |
| 48 | Auxiliary DC/DC power supplies | DC/DC stages provide the lower-voltage rails used by control and interface circuits. | U |
| 49 | Power and control PCB assemblies | Power and control boards carry switching, sensing, computation, and interface circuits. | L |
| 50 | Heat sink and drive enclosure | The heat sink removes heat from power devices. The enclosure protects the electronics. | L |

### Control, network and safety

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 51 | Real-time motor-control MCU or DSP | The microcontroller or DSP runs the real-time motor-control loops. | U |
| 52 | EtherCAT SubDevice controller | The controller handles EtherCAT frame processing and process-data exchange. | U |
| 53 | Ethernet PHY transceivers | Physical-layer transceivers send and receive Ethernet signals. | U |
| 54 | Port magnetics and connectors | Magnetics provide coupling and isolation. Connectors attach the network cables. | U |
| 55 | Configuration EEPROM | Nonvolatile memory stores device configuration in designs that use an external EEPROM. | U |
| 56 | Timing crystal or oscillator | The oscillator supplies a stable clock for control or communications. | U |
| 57 | Encoder interface circuitry | The circuitry receives encoder signals and passes position data to the controller. | L |
| 58 | Safe torque off circuitry | The safety circuit disables torque-producing output when safe torque off is requested. | L |
| 59 | Motor and DC power terminals | The terminals connect the motor phases and the DC supply. | U |
| 60 | CoE/CiA 402 firmware and ESI file | Firmware implements CAN application protocol over EtherCAT (CoE) and the CiA 402 drive profile. The EtherCAT SubDevice Information (ESI) file describes the device to configuration tools. | L |

[Deploy Robotic servo drive cutaway](https://deployrobotic.com/tour/#supply-servo-drive) · [TI 48 V inverter reference design](https://www.ti.com/tool/TIDA-01629) · [TI multi-axis EtherCAT reference design](https://www.ti.com/tool/TIDM-02006) · [EtherCAT implementation guide](https://www.ethercat.org/download/documents/ETG2200_V3i2i3_G_R_EtherCATImplementationGuide.pdf)

## Industrial fiber laser

Fiber-coupled pump diodes energize ytterbium-doped gain fiber. In the reference oscillator, two fiber Bragg gratings define the resonator. Delivery fiber carries laser output to a processing head that collimates and focuses it onto the work.

Early integration can include fiber handling and splicing, processing-head assembly, controls, cooling, and packaging. Verify optical loss, beam quality, cooling performance, contamination controls, and applicable laser-product safety requirements.

### Pump and optical path

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 61 | Fiber-coupled pump diode modules | Diode modules convert electrical power into pump light and couple it into fiber. | U |
| 62 | Pump diode current drivers | Current drivers regulate the electrical current supplied to the pump diodes. | L |
| 63 | Pump/signal fiber combiner | The combiner couples pump light into the gain-fiber path while passing the signal. | E |
| 64 | Ytterbium-doped double-clad fiber | The inner cladding guides pump light, and the doped core provides optical gain. | U |
| 65 | High-reflector fiber Bragg grating | The high-reflector grating reflects the selected wavelength back into the resonator. | E |
| 66 | Output-coupler fiber Bragg grating | The partially reflective grating lets a controlled portion of laser light exit the resonator. | E |
| 67 | Passive double-clad signal fiber | Passive fiber carries light between optical components without adding gain. | U |
| 68 | Cladding-light stripper | The stripper removes residual light propagating in the fiber cladding. | E |
| 69 | Fiber splices and protectors | Fusion splices join fibers optically. Protectors reinforce and shield the joints. | L |
| 70 | Beam sampler and monitor photodiode | The sampler diverts a small fraction of the beam for power monitoring by the photodiode. | U |

### Power, cooling and process head

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 71 | High-power delivery fiber cable | The cable routes high-power laser output from the source to the process head. | U |
| 72 | Delivery connector and end cap | The connector locates the fiber at the head, and the end cap manages optical intensity at the exit. | E |
| 73 | Output collimator assembly | The collimator converts the diverging fiber output into a near-parallel beam. | L |
| 74 | Focusing lens group | The lens group focuses the beam at the intended working distance. | E |
| 75 | Replaceable protective window | The replaceable window protects the focusing optics from process debris and contamination. | U |
| 76 | Cold plates and cooling manifold | Cold plates collect heat at components. The manifold distributes coolant. | L |
| 77 | Chiller, pump and heat exchanger | The cooling system circulates coolant and rejects heat from the laser system. | U |
| 78 | Power supply and laser controller | The supply powers the system, and the controller manages operating states and emission commands. | L |
| 79 | Interlock and emission safety circuit | The circuit monitors safety inputs and inhibits emission when required. | L |
| 80 | Process-head nozzle and gas hardware | The nozzle and gas hardware route shielding or process gas at the work area. | L |

[Deploy Robotic fiber laser cutaway](https://deployrobotic.com/tour/#supply-fiber-laser) · [Coherent high-power fiber laser devices](https://www.coherent.com/resources/application-note/components-and-accessories/specialty-optical-fibers/active-fiber-monolithic-high-power-fiber-laser-devices.pdf) · [Coherent high-power delivery fiber](https://www.coherent.com/news/blog/qbh-fiber-optic-cables) · [FDA laser product requirements](https://www.fda.gov/radiation-emitting-products/home-business-and-entertainment-products/laser-products-and-instruments)

## Machine-vision camera

The lens forms an image on a global-shutter CMOS sensor, which exposes the frame’s pixels together. The processing board turns the readout into image data and sends it over GigE Vision. Power over Ethernet (PoE) is optional in this reference design.

Start with board design and assembly, enclosure fabrication, sensor alignment, and optical calibration. Verify image quality using EMVA 1288 metrics where relevant, along with trigger timing, thermal performance, and interface interoperability.

### Sensor, optics and mechanics

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 81 | Global-shutter CMOS image sensor | The sensor converts light into pixel signals with a common exposure interval across the frame. | U |
| 82 | Sensor carrier PCB assembly | The carrier board supports the sensor and routes its readout, power, and timing signals. | L |
| 83 | Sensor positioning frame | The frame locates the sensor relative to the lens and optical axis. | L |
| 84 | Imaging lens elements | The lens elements form the image and control distortion and other aberrations. | E |
| 85 | Lens barrel and focus mechanism | The barrel locates the lenses, and the focus mechanism adjusts their optical position. | L |
| 86 | C-mount lens flange | The flange provides the mechanical interface and lens-to-sensor spacing for a C-mount lens. | L |
| 87 | Optical filter or IR-cut element | The filter shapes the wavelengths reaching the sensor, such as by rejecting infrared light. | U |
| 88 | Protective optical window | The window protects the sensor or internal optics while transmitting the intended wavelengths. | U |
| 89 | Sealed housing and gaskets | The enclosure and gaskets protect and seal the camera body. | L |
| 90 | Heat spreader and thermal interface | The heat spreader and interface conduct heat from electronics into the enclosure or heat sink. | L |

### Processing, network and power

| # | Subcomponent or build dependency | Function | Sourcing path |
| ---: | --- | --- | :---: |
| 91 | Image processor FPGA or SoC | An FPGA or system-on-chip handles sensor data, timing, and image processing. | U |
| 92 | Frame-buffer DRAM | DRAM provides temporary storage for frames or data queues. | U |
| 93 | Firmware flash memory | Flash memory stores firmware and other persistent data. | U |
| 94 | Image processor and I/O board | The board integrates processing, control, network, and external I/O circuits. | L |
| 95 | Ethernet PHY and port magnetics | The PHY drives the Ethernet link, and port magnetics provide coupling and isolation. | U |
| 96 | Locking Ethernet connector | The connector provides a mechanically secured network cable interface. | U |
| 97 | Power-over-Ethernet front end | The PoE circuitry extracts camera power from the Ethernet connection when used. | U |
| 98 | Sensor power regulators | Regulators supply the sensor’s required voltage rails. | U |
| 99 | Trigger and strobe I/O circuitry | Trigger and strobe circuits synchronize exposure and external lighting. | L |
| 100 | GigE Vision and GenICam firmware | Firmware streams images over GigE Vision and exposes camera controls through GenICam. | L |

[Deploy Robotic camera cutaway](https://deployrobotic.com/tour/#supply-industrial-camera) · [Basler global-shutter GigE camera example](https://www.baslerweb.com/en-us/shop/a2a4096-98g10c/) · [A3 GigE Vision standard](https://www.automate.org/vision/vision-standards/download-the-gige-vision-standard) · [EMVA 1288 camera characterization](https://www.emva.org/standards-technology/emva-1288/)
