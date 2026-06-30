# Vet Clinic & Pharmacy

The domain for a single local veterinary practice that operates both a clinic
(consultations, appointments) and a pharmacy/store (medications, equipment). It
is a **mixed practice**: it serves companion animals, ornamental birds, horses,
and livestock — not only pets. The site is a public Farsi/RTL presence plus a
logged-in client portal. It is NOT a multi-tenant product for many clinics.

The entire catalog and site navigation are organized **by Animal Category
first**, then by the kind of offering within it (see Section).

## Language

**Practice**:
The single veterinary clinic-and-pharmacy business that owns the site. There is
exactly one. Used for global settings, branding, hours, location.
_Avoid_: Tenant, organization, shop

**Owner**:
A customer of the Practice who holds a login account and owns one or more
Animals. The account holder and the party billed. May own companion pets OR
livestock/horses.
_Avoid_: Client, customer, user

**Animal**:
An animal belonging to an Owner; the subject of clinical care. Every Animal
belongs to one Animal Category and has a Species. When spoken of clinically it
is the "patient," but we use one term: Animal.
_Avoid_: Pet (a Pet is now one Animal Category, not the umbrella term), patient

**Animal Category**:
A top-level grouping that organizes the whole site and catalog. The current set:
Ornamental Birds (پرندگان زینتی), Companion Pets (حیوانات خانگی — cat, dog),
Equine (اسب — horse), Ruminants (نشخوارکنندگان — sheep, goat, camel). The home
page shows one image tile per Animal Category.
_Avoid_: Animal type, group

**Species**:
The specific kind of animal within a Category (cat, dog, horse, sheep, goat,
camel, …). A finer grain than Animal Category.
_Avoid_: Breed (breed is finer still and optional)

**Section**:
Within each Animal Category, offerings are split into four sections:
**Online Visit** (ویزیت آنلاین), **Medication** (دارو), **Equipment** (تجهیزات),
and **Service** (خدمات). A category's landing page presents these four. (Online
Visit is a single global booking surfaced here as an entry point, not bound to
the category — see Online Visit.)
_Avoid_: Tab, department; Consultation (renamed to Online Visit)

**Online Visit**:
A paid, time-boxed virtual visit with Staff (ویزیت آنلاین — formerly
"Consultation"). The Owner books a slot in advance and pays online at the moment
of booking; during the slot they ask whatever they like and get answers, and the
vet may issue an electronic Prescription. It is NOT tied to a specific registered
Animal — questions may be about any animal. Advice/answers only, no in-person
procedure.
_Avoid_: Consultation (renamed), مشاوره (use ویزیت آنلاین)

**Service**:
Something the clinic *does* for an Animal (خدمات) — a procedure or treatment such
as a wellness exam, vaccination, dental, or surgery. Distinct from a Consultation
(which is advice only). Requested via an Appointment.
_Avoid_: Treatment, procedure

**Product**:
A physical item the pharmacy/store sells: either a **Medication** (دارو, OTC or
prescription-only) or **Equipment** (تجهیزات — supplies, tools, accessories).
Has Animal Category, Section, name, price, and stock. Browsable by anyone.
_Avoid_: Item, SKU, good

**Prescription**:
An authorization, issued by a Veterinarian for a specific Animal, that permits
dispensing a prescription-only Medication. Created by Staff, not Owners.
_Avoid_: Script, Rx

**Refill Request**:
An Owner's request to have an existing Prescription dispensed again. Reviewed
and approved by Staff before it becomes payable.
_Avoid_: Refill order

**Appointment Request** / **Appointment**:
An Owner's submitted ask for a visit and the confirmed visit Staff create from it.
Two flavours: an in-person **Service** appointment (a chosen Animal + Service +
preferred times, Staff confirm, pay later) and a paid **Online Visit** (a booked
slot paid online up front, no Animal required). States: requested → confirmed →
completed / cancelled / no-show.
_Avoid_: Booking, reservation, slot

**Order**:
An Owner's purchase of one or more Products, collected in person at the pharmacy.
At launch, payment is settled at pickup (no gateway yet); once online payment is
enabled it is paid online before pickup. States: placed → (Rx approved) →
[paid] → ready-for-pickup → collected / cancelled.
_Avoid_: Cart, sale (a Cart is the pre-checkout draft only)

**Payment**:
An online payment for an Order or an Online Visit, made through an Iranian
payment gateway. States match the gateway callback: initiated → paid / failed,
plus refunded. Online payment is unavailable until the Practice obtains its
**e-Namad** (نماد الکترونیک), which itself requires the live site — so it arrives
after launch (see ADR-0005).
_Avoid_: Transaction, checkout

**Visit Record**:
The clinical note attached to a completed Appointment: date, offering, and the
vet's notes. An Animal's visit history is its list of Visit Records.
_Avoid_: Chart, encounter, EMR entry

**Vaccination**:
A record that an Animal received a specific vaccine on a date, with an optional
next-due date. Drives reminders.
_Avoid_: Shot, immunization record

**Staff**:
An employee of the Practice (veterinarian, technician, receptionist) who logs in
to manage everything. Distinct from an Owner.
_Avoid_: Admin, employee (when role matters, say Veterinarian / Receptionist)
