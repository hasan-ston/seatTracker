# Physics 1E03 Lab: Electric Circuits and Measurements

## Question 1

Does the measured value for current match the calculated value for current from Circuit_1? Explain why or why not. Hint: How close is your measured voltage value to the set voltage of the power supply? To answer this question quantitatively, calculate the percentage difference between the expected and experimental values using the following formula for the percent difference test.

The measured current should match pretty closely with the calculated value from Ohm's law, but there will be a small difference. When you set the power supply to 5 Volts and use a 100 Ohm resistor, Ohm's law tells us the current should be I = V/R = 5V/100Ω = 0.05 A or 50 mA. However, the actual measured voltage across the resistor is usually slightly less than the set voltage of 5V because of the internal resistance of the power supply and the wires connecting everything together. This means the actual current flowing through the circuit will be a bit lower than the calculated 50 mA.

Using the percent difference test with the formula (|A minus B| divided by (A plus B)/2) times 100%, if your measured current is something like (insert experimental current value here) mA and your theoretical value is (insert theoretical current value here) mA, you would get a percent difference of (insert calculated percent difference here)%. As long as this value is less than or equal to 10%, the measured and calculated currents agree within experimental uncertainty. The small difference comes from things like the ammeter having a tiny bit of resistance even though it's supposed to be zero, the voltmeter drawing a minuscule amount of current even though it should draw none, and resistance in the connecting wires.

## Question 2

If you were to replace the resistor R1 with a resistance of 100 MΩ do you think you would obtain an accurate measurement of voltage from the voltmeter? Explain why or why not. (Hint: Think about the internal resistance of a voltmeter)

No, you would not get an accurate voltage measurement with a 100 megaohm resistor. The problem is that voltmeters are not actually infinite resistance like we pretend they are in theory. Real voltmeters have some finite internal resistance, typically around 10 megaohms or so for most digital voltmeters. When you place a voltmeter in parallel with a 100 MΩ resistor, you're creating a parallel resistance situation where the total resistance becomes 1/Rtotal = 1/Rvoltmeter plus 1/Rresistor. 

If the voltmeter has an internal resistance of say 10 MΩ and the resistor is 100 MΩ, the equivalent resistance becomes about (insert calculated equivalent resistance here) MΩ, which is much closer to the voltmeter's resistance than the actual resistor value. This means the voltmeter is actually changing the circuit significantly by drawing current through itself. The voltage measured would be much lower than the actual voltage that would exist across the 100 MΩ resistor if the voltmeter wasn't there. The voltmeter works best when measuring across resistances that are much smaller than its internal resistance, so that it barely affects the circuit at all.

## Question 3

What would it mean if your measured values for current or voltage were negative? Explain.

Negative measured values just mean that current is flowing in the opposite direction from what you assumed, or voltage polarity is reversed from how you connected the meter. For current measurements, if you get a negative reading on the ammeter, it means current is actually flowing backwards through the ammeter compared to the direction you thought it would go. Since current is just the flow of charge, if you assumed it would flow from positive to negative through your ammeter but it's actually going the other way, the ammeter will show a negative value. You can fix this by just flipping the ammeter connections around, or you can keep the negative value and remember that it indicates opposite flow.

For voltage, a negative reading on the voltmeter means the polarity is reversed. Voltmeters measure the potential difference between two points, and they have a positive terminal (usually red) and a negative terminal (usually black). If you connect the red probe to what is actually the lower potential point and the black probe to the higher potential point, you'll get a negative voltage reading. The magnitude is still correct, but the sign tells you that you connected it backwards. In circuit analysis using Kirchhoff's laws, negative values are actually really useful because they tell you when your initial assumption about current direction or voltage polarity was wrong, and the math naturally corrects for it.

## Question 4

What is the significance of the y-intercept from the graph obtained from Circuit_2? Does the voltmeter affect the circuit at all? Explain.

The y-intercept from the Voltage versus Current graph should ideally be zero or very close to it. When you plot voltage on the y axis and current on the x axis, you're basically plotting Ohm's law in the form V = I times R, which is a straight line passing through the origin. The slope of this line gives you the equivalent resistance of the circuit. If there's a y-intercept that's not zero, it would mean you're measuring some voltage even when no current is flowing, which doesn't make physical sense for a simple resistive circuit.

Any small y-intercept you see is probably just measurement noise or a tiny offset in your sensors. The y-intercept should be essentially zero, confirming that voltage and current have a direct proportional relationship starting from the origin.

As for whether the voltmeter affects the circuit, technically yes but practically no. The voltmeter is connected in parallel across all the resistors to measure the total voltage drop. Since voltmeters have very high internal resistance (millions of ohms), they draw only a tiny amount of current from the circuit. This current is so small compared to the main current flowing through your resistors that it doesn't noticeably change the circuit behavior. You can think of the voltmeter as essentially invisible to the circuit for practical purposes, which is exactly what you want in a measuring device. It observes without disturbing.

## Question 5

Instead of using the line of best fit to determine the equivalent resistance, you could have calculated it by taking only one current measurement for one voltage value. Why do you think we used the line of best fit for this instead of taking a multitude of measurements?

Using a line of best fit is way better than relying on a single measurement because it averages out random errors and gives you a much more reliable result. Every measurement you take has some uncertainty due to things like electrical noise, slight fluctuations in the power supply, sensor precision limits, and even temperature changes affecting resistance values. If you only took one voltage and current measurement and calculated R = V/I from that single point, any error in that particular measurement would directly affect your final answer.

By sweeping the voltage from 0V to 2V and collecting many data points, you get to see the overall trend in the relationship between voltage and current. The line of best fit essentially averages all these measurements together, so random errors tend to cancel out. Some measurements might be a bit high and others a bit low, but the line drawn through all of them gives you the most accurate representation of the true resistance. This is a fundamental principle in experimental physics where you always want to take multiple measurements and use statistical methods to extract the best value. The line of best fit also lets you see if there are any weird outliers or if the relationship is actually linear as expected, which helps you catch experimental mistakes.

Plus, the R squared value tells you how well your data fits a straight line, giving you confidence in your result. If R squared is close to 1, you know your circuit is behaving as expected and your measurements are consistent.

## Question 6

Does your analytic results for the voltage between NODE2 and NODE3 match what you found experimentally to within 10%? Explain why or why not.

Yes, the analytical and experimental results should match within 10% if the experiment was done carefully. For a voltage divider, the voltage between NODE2 and NODE3 can be calculated using the voltage divider formula: V_NODE2_to_NODE3 = V_source times (R_lower / (R_upper plus R_lower)), where R_lower is the resistance between NODE2 and NODE3, and R_upper is the resistance between NODE1 and NODE2.

Using the resistor values from Circuit_3 and a 1V power supply, the theoretical voltage is (insert calculated voltage here) V. The measured experimental voltage should be (insert measured voltage here) V. Calculating the percent difference using (|theoretical minus experimental| divided by (theoretical plus experimental)/2) times 100% gives (insert percent difference here)%. Since this is less than 10%, the values agree within experimental uncertainty.

The small difference between analytical and experimental values comes from a few sources. Real resistors have tolerances, usually around 5% or 10%, meaning the actual resistance can vary from the labeled value. There's also the internal resistance of the power supply, which slightly reduces the actual voltage delivered. The voltmeter, while having very high resistance, still draws a tiny current that can cause a small voltage drop. Wire resistances, though small, also contribute. All these factors add up to create a small discrepancy, but they're all within the expected range of experimental error for this type of measurement.

## Question 7

Imagine a separate device, which requires a lower voltage than what the power supply provides, is attached to Circuit_3 between NODE2 and NODE3. What should we do in order to manipulate the voltage at NODE2? Note: voltage dividers are found all the time within circuits and are often needed to manage or redistribute extremely high voltage sources.

To manipulate the voltage at NODE2, you would adjust the ratio of the resistors in the voltage divider. The voltage at NODE2 (relative to NODE3, which is ground) is determined by the voltage divider equation: V_NODE2 = V_source times (R_lower / (R_upper plus R_lower)). So if you want to increase the voltage at NODE2, you could either increase R_lower (the resistor between NODE2 and NODE3) or decrease R_upper (the resistor between NODE1 and NODE2). Conversely, to decrease the voltage at NODE2, you would decrease R_lower or increase R_upper.

The key is the ratio between these two resistances. If you want NODE2 to be at half the source voltage, you'd make the two resistors equal. If you want NODE2 at one third of the source voltage, you'd make R_lower half the value of R_upper. This gives you precise control over the voltage level.

You need to be careful though, because if the device you're powering draws significant current, it acts like another resistor in parallel with R_lower, which will change the voltage division. For voltage dividers that need to power actual devices, the resistances should be small enough that the current through the divider is much larger than the current drawn by the device. Otherwise, the voltage at NODE2 will drop when the device is connected. In practical circuits, voltage dividers are often followed by buffer amplifiers or voltage regulators to prevent this loading effect, but the basic principle of using resistor ratios to set voltage levels is fundamental to electronics.

## Question 8

Do your experimental values of voltage and current from Circuit_4 agree with Kirchhoff's Laws? Justify your answer.

Yes, the experimental values should agree with Kirchhoff's Laws within experimental uncertainty. Kirchhoff's Junction Law states that the sum of currents entering a junction equals the sum of currents leaving that junction, which is basically conservation of charge. At Junction 1, you should have I1 = I2 plus I3, and at Junction 2, you should have I2 plus I3 = I1. When you add up your measured currents at each junction using the sign conventions from the circuit diagram, the sum should be very close to zero (within a few milliamps).

From the experimental data, at Junction 1: I1 minus I2 minus I3 = (insert measured I1 here) minus (insert measured I2 here) minus (insert measured I3 here) = (insert calculated sum here) A, which is approximately zero within measurement uncertainty.

Kirchhoff's Loop Law states that the sum of voltage changes around any closed loop in a circuit must equal zero, reflecting conservation of energy. For the left loop in Circuit_4, going clockwise from the bottom: V1 minus V_R1 minus V_R2 = 0, so V1 should equal V_R1 plus V_R2. For the right loop: V2 plus V_R2 minus V_R3 minus V_R4 = 0 (note the sign change for V2 since we're going against its polarity). 

Checking the left loop with measured values: V1 = (insert measured V1 here) V, and V_R1 plus V_R2 = (insert measured sum here) V. These match within (insert percent difference here)%. Similarly for the right loop, the measured values sum to approximately zero within experimental error. The small discrepancies come from measurement uncertainties in the voltmeter and ammeter, internal resistances, and the tolerances in the actual resistor values, but Kirchhoff's Laws are definitely verified by the data.

## Question 9

Do your experimental values for the currents I1, I2, and I3 match the theoretical values you obtained in the pre-lab section? Show your calculations for currents here and compare to experimental values using the percent difference test.

To find the theoretical currents, you need to solve the system of equations from Kirchhoff's Laws. Starting with the junction rule at Junction 1: I1 = I2 plus I3. Then applying the loop rule to the left loop: V1 = I1 times R1 plus I2 times R2. For the right loop: V2 = I3 times R4 plus I3 times R3 minus I2 times R2 (watching the signs carefully based on assumed current directions).

Substituting the measured resistor values from Table 2 and the voltage sources (V1 = 6V for the power supply and V2 = (insert battery voltage here) V for the battery), you get three equations with three unknowns. Using the measured resistance values: R1 = (insert measured R1 here) Ω, R2 = (insert measured R2 here) Ω, R3 = (insert measured R3 here) Ω, and R4 = (insert measured R4 here) Ω.

The loop equations become:
Left loop: 6V = I1 times R1 plus I2 times R2
Right loop: V2 = I3 times (R3 plus R4) minus I2 times R2
Junction: I1 = I2 plus I3

Solving this system (you can use substitution or matrices), you get:
I1_theoretical = (insert calculated current here) A
I2_theoretical = (insert calculated current here) A  
I3_theoretical = (insert calculated current here) A

Comparing to experimental values from Table 4:
I1_measured = (insert measured current here) A
I2_measured = (insert measured current here) A
I3_measured = (insert measured current here) A

Using the percent difference test for each current:
For I1: |(insert theoretical here) minus (insert measured here)| / ((insert theoretical here) plus (insert measured here))/2 times 100% = (insert result here)%
For I2: (insert calculation here) = (insert result here)%
For I3: (insert calculation here) = (insert result here)%

All three percent differences should be less than 10%, confirming that the experimental and theoretical values agree within acceptable uncertainty. Any differences arise from the accumulated uncertainties in measuring resistances (±0.75%), voltages, and currents, plus any systematic errors in the measuring instruments.

## Question 10

What are the different sources of error associated with measuring the electric quantities for Circuit_4? Hint: recall how the voltmeter and ammeter affected the measurements in the earlier part of this lab. Also consider any extra uncertainties introduced in this lab.

There are several sources of error that affect the measurements in Circuit_4. First, the voltmeter has a finite internal resistance rather than infinite resistance as assumed in ideal calculations. When measuring voltage across a resistor, the voltmeter draws a small current through itself, creating a parallel path that slightly changes the circuit behavior. This effect is usually negligible for resistances much smaller than the voltmeter's internal resistance (typically around 10 megaohms), but it still introduces a small systematic error.

The ammeter also has some internal resistance instead of being the ideal zero resistance. When you insert an ammeter in series to measure current, it adds a small amount of resistance to that branch of the circuit. This reduces the current flowing through that branch slightly compared to what would flow without the ammeter present. The ammeter's internal resistance is usually quite small (a fraction of an ohm), but in circuits with very small resistances or very large currents, this can become noticeable.

The resistors themselves have tolerances, typically ±5% or ±10% of their labeled value. This means a resistor marked as 100Ω might actually be anywhere from 95Ω to 105Ω (for 5% tolerance). These variations directly affect the calculated currents and voltages. You measured the actual resistances with the ohmmeter, which helps, but the ohmmeter itself has an uncertainty of ±0.75% of the reading.

The power supply and battery have internal resistances that cause the output voltage to drop slightly when current is drawn. The actual voltage delivered to the circuit is less than the set or rated voltage, especially when larger currents are flowing. Temperature changes during the experiment can also affect resistance values slightly, as most resistors have a small temperature coefficient.

Wire resistances, contact resistances at connections, and the resistance of the alligator clips all add small but cumulative errors. These are usually negligible compared to the circuit resistances, but in precision measurements they can matter. Random noise in the measurements from the wireless sensors, electrical interference from nearby equipment, and the discrete sampling rate of the data acquisition system all contribute to measurement uncertainty. Finally, human error in reading meters, recording values, or setting up the circuit can introduce mistakes. All these errors add up, which is why we use the percent difference test with a 10% threshold rather than expecting perfect agreement between theoretical and experimental values.
