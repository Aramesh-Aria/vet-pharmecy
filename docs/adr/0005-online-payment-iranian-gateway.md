# Online payment via an Iranian gateway, phased behind the e-Namad dependency

Online payment is the **target** model (at the stakeholder's request), but it
**cannot ship at launch**. An Iranian payment gateway requires an **e-Namad**
(نماد الکترونیک / e-trust seal), and e-Namad in turn requires a **live, working
website**. The dependency chain is therefore fixed:

> build & launch the site (no gateway) → obtain e-Namad → contract an Iranian
> gateway → enable online payment.

## What ships at launch (no gateway)

- **Store Orders:** payment is **settled at pickup** (interim). Owners place
  orders; Staff approve/price; the customer pays when collecting at the pharmacy.
- **Online Visit:** the paid virtual-visit feature is **held back** — it is
  intrinsically pay-online-at-booking, so it launches with the gateway, not before.

## What ships after e-Namad + gateway

- All Orders move to **pay-online-before-pickup** through an Iranian gateway
  (Zarinpal recommended; IDPay / Sadad / NextPay are alternatives behind the same
  interface).
- The **Online Visit** feature goes live: book a slot → pay online up front →
  attend → optional electronic Prescription.
- Prescription Medication keeps its **approve-then-pay** gate so customers never
  pay for an unauthorized drug.

## Design now so the swap is cheap

Build the `payments` app from the start with a single interface
(`start_payment(order)` + idempotent verify callback) and a **manual/pay-at-pickup
backend** for launch. Adding the real gateway later is then a new backend plus
enabling the online-pay step — no rework of Order or checkout code.

**Consequences:** the e-Namad application needs accurate business identity pages
(contact, address, terms) live before applying — so those pages are pre-launch
scope. The redirect→callback→verify round trip must be idempotent, and Order
state must reconcile with gateway state, including refunds. Settlement is in Rial/
Toman.
