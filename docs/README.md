# POS Next Documentation

Welcome to the POS Next documentation directory. This folder contains comprehensive guides for developers and contributors.

## 📚 Available Documentation

### User Guides
- **[LOCALIZATION.md](LOCALIZATION.md)** - Language settings guide
  - Configuring allowed languages
  - Using the language switcher
  - Available languages
  - Troubleshooting

- **[Wallet-Loyalty-User-Guide.md](Wallet-Loyalty-User-Guide.md)** - Wallet and loyalty system user guide

- **[OFFERS_AND_PROMOTIONS.md](OFFERS_AND_PROMOTIONS.md)** - Offers and promotions system
  - Pricing Rules and Promotional Schemes integration
  - Mixed Conditions configuration
  - Frontend architecture (stores, flow)
  - Backend API reference
  - Troubleshooting guide

### Architecture
- **[STARTUP_SEQUENCE.md](STARTUP_SEQUENCE.md)** - Application initialization flow
  - PWA service worker registration
  - Parallel authentication (CSRF + User)
  - Bootstrap data preloading
  - Performance optimizations
  - Offline worker integration

- **[OFFLINE_SYNC.md](OFFLINE_SYNC.md)** - Offline invoice synchronization system
  - Architecture overview
  - Deduplication mechanism (offline_id)
  - Data flow diagrams
  - API reference
  - IndexedDB schema
  - Troubleshooting guide

- **[PRICING_AND_SUBMISSION.md](PRICING_AND_SUBMISSION.md)** - Pricing and invoice submission flow
  - Rate vs Price List Rate concepts
  - Tax modes (inclusive/exclusive)
  - Discount handling (item-level and cart-level)
  - Frontend and backend function reference
  - Offline mode pricing
  - Pricing rules integration
  - Troubleshooting guide

### Version Control
- **[UPSTREAM_REVIEW_2026-07-29.md](UPSTREAM_REVIEW_2026-07-29.md)** - Review of official `develop` changes
  - Adopted correctness fixes
  - Deferred high-risk pricing changes
  - Digit-owned upstream synchronization policy

- **[DIGITPOS_SOURCE_OF_TRUTH.md](DIGITPOS_SOURCE_OF_TRUTH.md)** - Canonical Digit POS source and deployment topology
  - Development and production checkout responsibilities
  - `posnext` versus `pos_next` naming
  - Current purchasing, supplier payment, catalog, and reporting baseline
  - Safe build, migration, verification, and recovery workflow

- **[PROJECT_MEMORY.md](PROJECT_MEMORY.md)** - Durable development-program memory
  - Protected production boundary and current verified state
  - Engineering rules, definition of done, and progress ledger
  - Resume protocol for new development sessions

- **[DEVELOPMENT_MASTER_PLAN.md](DEVELOPMENT_MASTER_PLAN.md)** - Complete milestone plan
  - Feature-flag architecture and dependency model
  - Reports, purchasing, offline, payments, gift cards, loyalty, and restock roadmap
  - Acceptance criteria, test strategy, and delivery order

- **[SOL_5_6_EXECUTION_PROMPT.md](SOL_5_6_EXECUTION_PROMPT.md)** - Dedicated Sol 5.6 handoff prompt
  - One-branch execution policy
  - Production protection rules
  - Required first implementation milestones

- **[VERSION_CONTROL.md](VERSION_CONTROL.md)** - Complete guide to the version control system
  - Architecture overview
  - Version types and strategies
  - Build process details
  - Release procedures
  - API reference
  - Troubleshooting

- **[QUICKSTART_VERSION.md](QUICKSTART_VERSION.md)** - Quick reference for version management
  - Common commands
  - Quick workflows
  - File locations
  - Troubleshooting tips

## 🚀 Quick Links

### For Developers

**Check current version:**
```bash
cd /home/ubuntu/frappe-bench
bench --site nexus.local execute pos_next.utils.get_app_version
```

**Bump version:**
```bash
cd /home/ubuntu/frappe-bench/apps/pos_next
./scripts/version-bump.sh patch  # or minor/major
```

**Build frontend:**
```bash
cd POS
yarn build
```

### For Contributors

- See [VERSION_CONTROL.md](VERSION_CONTROL.md) for release process
- See [QUICKSTART_VERSION.md](QUICKSTART_VERSION.md) for common tasks

## 📝 Documentation Structure

```
docs/
├── README.md                        # This file
├── DIGITPOS_SOURCE_OF_TRUTH.md      # Canonical source and deployment workflow
├── UPSTREAM_REVIEW_2026-07-29.md    # Official develop review and adoption record
├── LOCALIZATION.md                  # Language settings user guide
├── OFFERS_AND_PROMOTIONS.md         # Offers and promotions system
├── OFFLINE_SYNC.md                  # Offline invoice sync system
├── PRICING_AND_SUBMISSION.md        # Pricing and invoice submission flow
├── STARTUP_SEQUENCE.md              # Application initialization flow
├── VERSION_CONTROL.md               # Comprehensive version control guide
├── QUICKSTART_VERSION.md            # Quick reference guide
├── Wallet-System-Technical-Guide.md # Wallet system technical docs
└── Wallet-Loyalty-User-Guide.md     # Wallet and loyalty user guide
```

## 🔗 External Resources

- [POS Next Repository](https://github.com/your-org/pos_next)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [Vite Documentation](https://vitejs.dev)

## 📧 Support

For questions or issues:
- Open an issue on GitHub
- Contact: support@brainwise.me

## 🤝 Contributing

When adding new documentation:
1. Place `.md` files in this `docs/` folder
2. Update this README with links to new docs
3. Follow the existing documentation style
4. Include code examples where appropriate
5. Add troubleshooting sections
