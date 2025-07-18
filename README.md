# PDC-Project

## Overview
Building a **Parallel Distributed Crawler (PDC)** to scrape **live flight ticket prices** across different city pairs.
Currently we will try to build a database for the tickets since no past data of tickets currently exists.

---

## ✈️ Websites for Scraping

| Website             | Pros                                           | Cons                                  | Difficulty        |
|---------------------|-------------------------------------------------|--------------------------------------|-------------------|
| **Skyscanner**       | Easy to search ANY route; API-like structure   | Some bot detection                   | Moderate          |
| **Google Flights**   | Very rich data; many airlines                  | Heavy JavaScript, dynamic loading    | Hard (needs Selenium) |
| **Momondo**          | Simple interface; shows many prices together  | Some popups/redirects                | Easy              |
| **Kayak**            | Shows flexible dates, cheap days              | Anti-scraping if too fast            | Moderate          |
| **Expedia**          | Famous; flights + hotels bundles              | Cluttered page, harder to parse      | Moderate-Hard     |
| **FlightAware**      | Shows real-time flights                       | Focuses more on flights, not ticket costs | Moderate     |
| **Travelocity / Orbitz** | Expedia-owned, similar                   | Same issues as Expedia               | Moderate          |
| **CheapOair**        | Special deals; multiple airlines              | Ads and distractions                 | Moderate          |
| **Kiwi.com**         | Flexible routes search                        | Complex HTML DOM                     | Moderate          |
| **Hopper**           | Good for predictions                          | No easy public scraping (app-based)  | Hard              |

---

## 🛢️ MongoDB Setup
currently need to setup a mongoDB connection 
and setup a naive scrapper to test 
Selenium 

- Install pymongo:
```bash
pip install pymongo
```
## 🛢️ MongoDB Setup
```bash

pip install selenium
```
