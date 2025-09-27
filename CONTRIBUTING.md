# Contributing to AI Long/Short Investment Club

Thank you for your interest in contributing to the AI Long/Short Investment Club platform! This project aims to provide educational resources for learning about AI disruption investment strategies.

## 🎯 Project Goals

- **Educational Focus**: Provide learning tools for investment strategy concepts
- **Global Accessibility**: Support multiple brokers and markets worldwide
- **Compliance**: Maintain educational positioning without providing investment advice
- **Open Source**: Enable community contributions and improvements

## 🤝 How to Contribute

### Types of Contributions Welcome

1. **Bug Reports**: Help us identify and fix issues
2. **Feature Requests**: Suggest new educational features
3. **Documentation**: Improve guides and explanations
4. **Code Improvements**: Enhance functionality and performance
5. **Broker Integrations**: Add support for additional brokers
6. **Educational Content**: Contribute learning materials

### Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/ai-longshort-investment-club.git
   cd ai-longshort-investment-club
   ```

2. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run in Demo Mode**
   ```bash
   python app.py
   ```
   Visit http://localhost:5000 to see the platform

### Development Guidelines

#### Code Standards
- **Python**: Follow PEP 8 style guidelines
- **JavaScript**: Use ES6+ features and consistent formatting
- **HTML/CSS**: Semantic markup and responsive design
- **Comments**: Clear documentation for complex logic

#### Educational Focus
- All features must maintain educational positioning
- Include appropriate disclaimers and risk warnings
- Avoid language that could be construed as investment advice
- Emphasize user responsibility and independent decision-making

#### Security Requirements
- Never commit API keys or credentials
- Use environment variables for sensitive configuration
- Implement proper input validation and sanitization
- Follow secure coding practices

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clear, focused commits
   - Include tests for new functionality
   - Update documentation as needed

3. **Test Thoroughly**
   - Test in demo mode without API credentials
   - Verify educational disclaimers are present
   - Check responsive design on mobile devices
   - Validate all forms and user interactions

4. **Submit Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Include screenshots for UI changes
   - Ensure all tests pass

### Issue Reporting

When reporting bugs or requesting features, please include:

- **Clear Description**: What happened vs. what was expected
- **Steps to Reproduce**: Detailed steps to recreate the issue
- **Environment**: Browser, OS, Python version
- **Screenshots**: Visual evidence of the issue
- **Educational Impact**: How it affects the learning experience

### Broker Integration Guidelines

When adding support for new brokers:

1. **Research Compliance**: Ensure broker allows educational/demo use
2. **API Documentation**: Verify API availability and terms
3. **Demo Mode**: Implement full functionality without real credentials
4. **Symbol Mapping**: Handle different symbol formats appropriately
5. **Error Handling**: Graceful fallbacks when API is unavailable

### Documentation Standards

- **User Guides**: Step-by-step instructions with screenshots
- **Technical Docs**: API references and implementation details
- **Legal Compliance**: Appropriate disclaimers and risk warnings
- **Examples**: Code samples and configuration examples

## 📋 Code of Conduct

### Our Standards

- **Respectful Communication**: Be kind and professional
- **Educational Focus**: Keep discussions centered on learning
- **Inclusive Environment**: Welcome contributors of all backgrounds
- **Constructive Feedback**: Provide helpful, actionable suggestions

### Unacceptable Behavior

- Investment advice or recommendations
- Harassment or discriminatory language
- Sharing of real trading credentials
- Promotion of specific financial products
- Spam or off-topic discussions

## 🛡️ Legal and Compliance

### Important Reminders

- This project is for **educational purposes only**
- Contributors must not provide investment advice
- All features must include appropriate disclaimers
- Maintain clear separation between education and advice
- Respect broker terms of service and API usage limits

### Liability

Contributors acknowledge that:
- This software is provided "as is" without warranties
- No investment advice or recommendations are provided
- Users are responsible for their own investment decisions
- Contributors are not liable for any financial outcomes

## 🚀 Development Roadmap

### Current Priorities

1. **Additional Broker Support**: Interactive Brokers, Charles Schwab
2. **Mobile App**: React Native implementation
3. **Advanced Analytics**: Portfolio performance tracking
4. **Social Features**: Investment club collaboration tools

### Future Enhancements

- Real-time market data integration
- Advanced charting and visualization
- Multi-language support
- Institutional broker support

## 📞 Getting Help

- **Documentation**: Check the `/docs` folder for guides
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Report security issues privately via email

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Documentation credits
- Community highlights

Thank you for helping make investment education more accessible worldwide!

---

**Remember**: This project is about education, not investment advice. All contributions should maintain this focus and include appropriate disclaimers.

