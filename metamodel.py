"""
NFR Framework - 3-Level Metamodel Architecture (Version 2)
===========================================================

Level 1: METAMODEL (Ontology) - Metaclasses define structure
Level 2: MODEL (Classes) - Instances of metaclasses  
Level 3: GROUND INSTANCES (Tokens) - Concrete occurrences

"""

from typing import List, Dict, Any, Optional
from enum import Enum
import inspect
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# ============================================================================
# LEVEL 1: METAMODEL (Ontology) - METACLASSES
# ============================================================================

class PropositionMetaClass(type):
    """
    Metaclass for all propositions.
    Defines: priority, label
    """
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # Always create new set (don't share with parent)
        parent_attrs = set()
        if hasattr(cls, '_metaclass_attributes'):
            parent_attrs = cls._metaclass_attributes.copy()
        cls._metaclass_attributes = parent_attrs | {'priority', 'label'}
        return cls


class SoftgoalMetaClass(PropositionMetaClass):
    """
    Metaclass for softgoals.
    Defines: type, topic (+ priority, label from parent)
    """
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # Copy parent's attributes (don't share the same set!)
        parent_attrs = set()
        if hasattr(cls, '_metaclass_attributes'):
            parent_attrs = cls._metaclass_attributes.copy()
        # Create new set with parent + new attributes
        cls._metaclass_attributes = parent_attrs | {'type', 'topic'}
        return cls


class NFRSoftgoalMetaClass(SoftgoalMetaClass):
    """Metaclass for NFR softgoals"""
    pass


class OperationalizingSoftgoalMetaClass(SoftgoalMetaClass):
    """Metaclass for operationalizing softgoals"""
    pass


class ClaimSoftgoalMetaClass(SoftgoalMetaClass):
    """Metaclass for claim softgoals"""
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # ClaimSoftgoal has ONLY type and topic (no description, label, priority)
        cls._metaclass_attributes = {'type', 'topic'}
        return cls


class SoftgoalTypeMetaClass(type):
    """Metaclass for softgoal types"""
    pass


class SoftgoalTopicMetaClass(type):
    """Metaclass for softgoal topics"""
    pass


class ContributionMetaClass(PropositionMetaClass):
    """Metaclass for contributions"""
    pass


class MethodMetaClass(type):
    """Metaclass for methods"""
    pass


class DecompositionMethodMetaClass(MethodMetaClass):
    """Metaclass for decomposition methods"""
    pass

class NFRDecompositionMethodMetaClass(DecompositionMethodMetaClass):
    """Metaclass for decomposition methods"""
    pass

class OperationalizationDecompositionMethodMetaClass(DecompositionMethodMetaClass):
    """Metaclass for decomposition methods"""
    pass
class ClaimDecompositionMethodMetaClass(DecompositionMethodMetaClass):
    """Metaclass for decomposition methods"""
    pass


# ============================================================================
# LEVEL 2: MODEL - CLASSES
# ============================================================================

# ----------------------------------------------------------------------------
# Enums and Base Types
# ----------------------------------------------------------------------------

class PropositionPriority(Enum):
    """Priority levels for propositions"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class PropositionLabel(Enum):
    """Labels for proposition satisfaction"""
    SATISFICED = "satisficed"
    DENIED = "denied"
    WEAKLY_SATISFICED = "weakly_satisficed"
    WEAKLY_DENIED = "weakly_denied"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"


class ContributionType(Enum):
    """Types of contributions"""
    MAKE = "MAKE"
    HELP = "HELP"
    SOME_PLUS = "SOME+"
    UNKNOWN = "UNKNOWN"
    SOME_MINUS = "SOME-"
    HURT = "HURT"
    BREAK = "BREAK"


# ----------------------------------------------------------------------------
# Base Classes
# ----------------------------------------------------------------------------

class Proposition(metaclass=PropositionMetaClass):
    """Base class for all propositions"""
    def __init__(self):
        self.priority = PropositionPriority.MEDIUM
        self.label = PropositionLabel.UNKNOWN
        self.description = ""


class Softgoal(Proposition, metaclass=SoftgoalMetaClass):
    """
    Base class for all softgoals.
    
    Note the syntax:
    - Softgoal(Proposition) = inheritance (isA) - Softgoal inherits from Proposition
    - metaclass=SoftgoalMetaClass = instanceOf - Softgoal is instance of SoftgoalMetaClass
    """
    def __init__(self):
        super().__init__()
        self.type = None
        self.topic = None


class NFRSoftgoal(Softgoal, metaclass=NFRSoftgoalMetaClass):
    """NFR Softgoal class"""
    pass


class OperationalizingSoftgoal(Softgoal, metaclass=OperationalizingSoftgoalMetaClass):
    """Operationalizing Softgoal class"""
    pass


class ClaimSoftgoal(Softgoal, metaclass=ClaimSoftgoalMetaClass):
    """
    Claim Softgoal class.
    Used for argumentation and attribution of decomposition methods.
    
    ClaimSoftgoal only has TWO attributes:
    - TYPE: The claim itself (a ClaimSoftgoalType class)
    - TOPIC: What the claim is about (a SoftgoalTopic)
    
    Example:
        claim = ClaimSoftgoal()
        claim.type = SmithPerformanceClaimType  # The claim: "According to Smith's..."
        claim.topic = SoftgoalTopic("Performance Decomposition")  # What it's about
    """
    def __init__(self):
        # Don't call super().__init__() to avoid getting description, label, priority
        self.type = None
        self.topic = None


class SoftgoalTopic:
    """Topic/domain of a softgoal"""
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return f"SoftgoalTopic('{self.name}')"


# ----------------------------------------------------------------------------
# Softgoal Type Classes
# ----------------------------------------------------------------------------

class SoftgoalType(metaclass=SoftgoalTypeMetaClass):
    """Base class for all softgoal types"""
    description = "Base type for softgoals"


class NFRSoftgoalType(SoftgoalType):
    """Base class for NFR quality attribute types"""
    pass


class OperationalizingSoftgoalType(SoftgoalType):
    """Base class for operationalizing technique types"""
    pass


class ClaimSoftgoalType(SoftgoalType):
    """Base class for claim types"""
    pass


# Specific Claim Types (the claim is the type itself)
class SmithPerformanceClaimType(ClaimSoftgoalType):
    """Claim type for Smith's user-centered performance metrics"""
    description = "According to Smith's User-Centered Performance Metrics"


class CIATriadClaimType(ClaimSoftgoalType):
    """Claim type for CIA Triad security decomposition"""
    description = "Trusted Computer System Evaluation Criteria (TCSEC/Orange Book, 1985) - Defines security through Confidentiality, Integrity, and Availability"


class WindowsTaskManagerClaimType(ClaimSoftgoalType):
    """Claim type for Windows Task Manager performance metrics"""
    description = "Microsoft Windows Task Manager - Performance Tab"


class TraditionalCSPerformanceClaimType(ClaimSoftgoalType):
    """Claim type for traditional CS performance decomposition"""
    description = "Traditional Computer Science - Time and Space Complexity"

class WikipediaEncryptionTypesClaimType(ClaimSoftgoalType):
    """Claim type for types of encryptions"""
    description = "Wikipedia (Encryption article) - Classifies encryption into Symmetric-key and Public-key (asymmetric) schemes"

class ChungNFRFrameworkClaimType(ClaimSoftgoalType):
    """Claim type for Chung et al.'s NFR Framework"""
    description = "According to Chung et al.'s NFR Framework (2000)"

class ISO25010UsabilityClaimType(ClaimSoftgoalType):
    """Claim type for ISO 25010 Usability decomposition"""
    description = "ISO/IEC 25010:2011 Systems and software Quality Requirements and Evaluation (SQuaRE) - Defines usability through five quality sub-characteristics"

class ManduchiSafetyClaimType(ClaimSoftgoalType):
    """Claim type for Manduchi et al. safety-focused design"""
    description = "Manduchi et al. (2024). Smartphone apps for indoor wayfinding for blind users. ACM Transactions on Accessible Computing - Advance warnings minimize input to focus on safety"

class ManduchiUsabilityClaimType(ClaimSoftgoalType):
    """Claim type for Manduchi et al. usability design"""
    description = "Manduchi et al. (2024). Smartphone apps for indoor wayfinding for blind users - Multimodal feedback enables hands-free operation"

class ASSISTUsabilityClaimType(ClaimSoftgoalType):
    """Claim type for ASSIST personalization study"""
    description = "ASSIST (2020). Indoor navigation assistant for blind and visually impaired people - Personalized interfaces improve usability by adapting to unique user experiences"

class PMCCognitiveLoadClaimType(ClaimSoftgoalType):
    """Claim type for PMC multimodal review on cognitive load"""
    description = "PMC (2024). Comprehensive review on NUI, multi-sensory interfaces for visually impaired users - Concise audio reduces cognitive overburden"

class PMCReceptivityClaimType(ClaimSoftgoalType):
    """Claim type for PMC multimodal review on receptivity"""
    description = "PMC (2024). Comprehensive review on NUI, multi-sensory interfaces for visually impaired users - Non-speech sounds improve receptivity"

class SensorsSafetyClaimType(ClaimSoftgoalType):
    """Claim type for Sensors 2012 positioning accuracy"""
    description = "Sensors (2012). An Indoor Navigation System for the Visually Impaired - Positioning accuracy of ≤0.4m enables safe navigation"

class PouloseSensorFusionClaimType(ClaimSoftgoalType):
    """Claim type for Poulose & Kim sensor fusion framework"""
    description = "Poulose & Kim (2019). A Sensor Fusion Framework for Indoor Localization Using Smartphone Sensors - Sensor fusion reduces positioning error to 0.44-1.17m"

class NielsenLearnabilityClaimType(ClaimSoftgoalType):
    """Claim type for Nielsen Norman Group learnability metrics"""
    description = "Nielsen Norman Group (2019). How to Measure Learnability of a User Interface - Steep learning curves enable proficiency within approximately 4 trials"


# NFR Quality Attribute Types
class PerformanceType(NFRSoftgoalType):
    """Performance quality attribute type"""
    description = "System response time, throughput, and efficiency; system operation speed/performance; optimality"


class TimePerformanceType(NFRSoftgoalType):
    """Time-related performance type"""
    description = "Performance quality related to time or temporal aspects; how fast operations complete; speed and quickness; time efficiency"


class SpacePerformanceType(NFRSoftgoalType):
    """Space-related performance type"""
    description = "Performance quality related to space or memory usage"


class ResponsivenessPerformanceType(NFRSoftgoalType):
    """User-perceived responsiveness type (Smith's approach)"""
    description = "User-perceived system responsiveness and interactivity"


# Windows Task Manager Performance Types
class CPUUtilizationType(NFRSoftgoalType):
    """CPU utilization performance type (Windows Task Manager)"""
    description = "Processor usage and computational performance"


class MemoryUsageType(NFRSoftgoalType):
    """Memory usage performance type (Windows Task Manager)"""
    description = "RAM utilization and memory consumption"


class DiskTimeType(NFRSoftgoalType):
    """Active disk time performance type (Windows Task Manager)"""
    description = "Disk I/O activity and storage access time"


class NetworkThroughputType(NFRSoftgoalType):
    """Network throughput performance type (Windows Task Manager)"""
    description = "Network bandwidth utilization and data transfer rate"


class GPUUtilizationType(NFRSoftgoalType):
    """GPU utilization performance type (Windows Task Manager)"""
    description = "Graphics processor usage and rendering performance"


class SecurityType(NFRSoftgoalType):
    """Security quality attribute type"""
    description = "Protection from unauthorized access and threats"


class ConfidentialityType(NFRSoftgoalType):
    """Confidentiality security type"""
    description = "Protecting information from unauthorized disclosure"


class IntegrityType(NFRSoftgoalType):
    """Integrity security type"""
    description = "Protecting information from unauthorized modification"


class AvailabilityType(NFRSoftgoalType):
    """Availability security type"""
    description = "Ensuring systems and data are accessible when needed ubiquitous access; available everywhere and anywhere; universal availability; always accessible; system uptime and continuous operation"


class UsabilityType(NFRSoftgoalType):
    """Usability quality attribute type"""
    description = "Ease of use and user experience; comfortable interaction; user-friendly interface; easy to learn and use; intuitive design; pleasant and convenient user experience"


class ReliabilityType(NFRSoftgoalType):
    """Reliability quality attribute type"""
    description = "System dependability and consistency"


class MaintainabilityType(NFRSoftgoalType):
    """Maintainability quality attribute type"""
    description = "Ease of system maintenance and evolution"


# Additional NFR Quality Attribute Types (alphabetically ordered)
class AccuracyType(NFRSoftgoalType):
    """Accuracy quality attribute type"""
    description = "The number of correctly predicted data points out of all the data points"


class AdaptabilityType(NFRSoftgoalType):
    """Adaptability quality attribute type"""
    description = "The ability of a system to work well in different but related contexts; automatic adjustment to different environments; operates across various platforms and conditions; context-aware behavior"


class BiasType(NFRSoftgoalType):
    """Bias quality attribute type"""
    description = "A phenomenon that occurs when an algorithm produces results that are systematically prejudiced due to erroneous assumptions in the ML process"


class CompletenessType(NFRSoftgoalType):
    """Completeness quality attribute type"""
    description = "An indication of the comprehensiveness of available data, as a proportion of the entire data set, to address specific information requirements"


class ComplexityType(NFRSoftgoalType):
    """Complexity quality attribute type"""
    description = "When a system or solution has many components, interrelations or interactions, and is difficult to understand"


class ConsistencyType(NFRSoftgoalType):
    """Consistency quality attribute type"""
    description = "A series of measurements of the same project carried out by different raters using the same method should produce similar results"


class CorrectnessType(NFRSoftgoalType):
    """Correctness quality attribute type"""
    description = "The output of the system matches the expectations outlined in the requirements, and the system operates without failure"


class DomainAdaptationType(NFRSoftgoalType):
    """Domain Adaptation quality attribute type"""
    description = "The ability of a model trained on a source domain to be used in a different—but related—domain"


class EfficiencyType(NFRSoftgoalType):
    """Efficiency quality attribute type"""
    description = "The ability to accomplish something with minimal time and effort, resource amount used in relation to the results achieved"


class EthicsType(NFRSoftgoalType):
    """Ethics quality attribute type"""
    description = "Concerned with adding or ensuring moral behaviors"


class ExplainabilityType(NFRSoftgoalType):
    """Explainability quality attribute type"""
    description = "The extent to which the internal mechanics of ML-enabled system can be explained in human terms"


class FairnessType(NFRSoftgoalType):
    """Fairness quality attribute type"""
    description = "The ability of a system to operate in a fair and unbiased manner"


class FaultToleranceType(NFRSoftgoalType):
    """Fault Tolerance quality attribute type"""
    description = "The ability of a system to continue operating without interruption when one or more of its components fail"


class FlexibilityType(NFRSoftgoalType):
    """Flexibility quality attribute type"""
    description = "The ability of a system to react/adapt to changing demands or conditions; ; user can configure and tailor settings; support for individual preferences; flexible configuration options"


class InterpretabilityType(NFRSoftgoalType):
    """Interpretability quality attribute type"""
    description = "The extraction of relevant knowledge from a model concerning relationships either contained in data or learned by the model"


class InteroperabilityType(NFRSoftgoalType):
    """Interoperability quality attribute type"""
    description = "The ability for two systems to communicate effectively"


class JustifiabilityType(NFRSoftgoalType):
    """Justifiability quality attribute type"""
    description = "The ability to show the output of an ML-enabled system to be right or reasonable"


class PortabilityType(NFRSoftgoalType):
    """Portability quality attribute type"""
    description = "The ability to transfer a system or element of a system from one environment to another"


class PrivacyType(NFRSoftgoalType):
    """Privacy quality attribute type"""
    description = "An algorithm is private if an observer examining the output is not able to determine whether a specific individual's information was used in the computation"


class RepeatabilityType(NFRSoftgoalType):
    """Repeatability quality attribute type"""
    description = "The variation in measurements taken by a single instrument or person under the same conditions"


class RetrainabilityType(NFRSoftgoalType):
    """Retrainability quality attribute type"""
    description = "The ability to re-run the process that generated the previously selected model on a new training set of data"


class ReproducibilityType(NFRSoftgoalType):
    """Reproducibility quality attribute type"""
    description = "One can repeatedly run your algorithm on certain datasets and obtain the same (or similar) results"


class ReusabilityType(NFRSoftgoalType):
    """Reusability quality attribute type"""
    description = "The ability of reusing the whole or the greater part of the system component for similar but different purpose"


class SafetyType(NFRSoftgoalType):
    """Safety quality attribute type"""
    description = "The absence of failures or conditions that render a system dangerous; protection from harm, hazards, and unsafe conditions; ensuring safe operation and navigation; preventing accidents and injury to users"


class ScalabilityType(NFRSoftgoalType):
    """Scalability quality attribute type"""
    description = "The ability to increase or decrease the capacity of the system in response to changing demands"


class TestabilityType(NFRSoftgoalType):
    """Testability quality attribute type"""
    description = "The ability of the system to support testing by offering relevant information or ensuring the visibility of failures"


class TransparencyType(NFRSoftgoalType):
    """Transparency quality attribute type"""
    description = "The extent to which a human user can infer why the system made a particular decision or produced a particular externally-visible behaviour"


class TraceabilityType(NFRSoftgoalType):
    """Traceability quality attribute type"""
    description = "The ability to trace work items across the development lifecycle"


class TrustType(NFRSoftgoalType):
    """Trust quality attribute type"""
    description = "A trusted system is a system that is relied upon to a specified extent to enforce a specified security, or a security policy"


class LegalComplianceType(NFRSoftgoalType):
    """Legal Compliance type"""
    description = "Legal requirements, regulatory compliance, contractual obligations, and adherence to laws and standards"


class LookFeelType(NFRSoftgoalType):
    """Look and Feel type"""
    description = "Visual appearance, UI aesthetics, design appeal, user interface look and style; comfortable visual experience; pleasing presentation; attractive design"

# New NFR Types from Taxonomy
class RecoverabilityType(NFRSoftgoalType):
    """Recoverability quality attribute type"""
    description = "Ability of the system to recover from failures and restore normal operation"

class DiagnosabilityType(NFRSoftgoalType):
    """Diagnosability quality attribute type"""
    description = "Ease of identifying, isolating, and troubleshooting system problems"

class CompatibilityType(NFRSoftgoalType):
    """Compatibility quality attribute type"""
    description = "Ability to work with existing systems, data formats, and standards"

class DeterministicBehaviorType(NFRSoftgoalType):
    """Deterministic Behavior quality attribute type"""
    description = "Predictable, repeatable system behavior given the same inputs"

class LearnabilityType(NFRSoftgoalType):
    """Learnability quality attribute type (ISO 25010)"""
    description = "Degree to which a system can be used by specified users to achieve specified goals of learning to use the system with effectiveness, efficiency, freedom from risk and satisfaction"

class MemorabilityType(NFRSoftgoalType):
    """Memorability quality attribute type (ISO 25010)"""
    description = "Degree to which a system can be remembered by users after a period of non-use"

class ErrorPreventionType(NFRSoftgoalType):
    """Error Prevention quality attribute type (ISO 25010)"""
    description = "Degree to which a system prevents users from making errors"

class SatisfactionType(NFRSoftgoalType):
    """Satisfaction quality attribute type (ISO 25010)"""
    description = "Degree to which user needs are satisfied when a system is used in a specified context of use"


# Operationalizing Technique Types
class IndexingType(OperationalizingSoftgoalType):
    """Indexing technique type"""
    description = "Using database indexes to improve query performance"


class CachingType(OperationalizingSoftgoalType):
    """Caching technique type"""
    description = "Storing frequently accessed data in cache"


class EncryptionType(OperationalizingSoftgoalType):
    """Encryption technique type"""
    description = "Encrypting data to protect confidentiality"

class SymmetricKeyEncryptionType(EncryptionType):
    """Symmetric-key encryption - same key for encryption and decryption"""
    pass

class PublicKeyEncryptionType(EncryptionType):
    """Public-key (asymmetric) encryption - different keys for encryption and decryption"""
    pass

class RSAEncryptionType(PublicKeyEncryptionType):
    """RSA public-key encryption"""
    pass

class AuditingType(OperationalizingSoftgoalType):
    """Auditing technique type"""
    description = "Recording system events, activities, or data changes for compliance and verification"

class ExceptionHandlingType(OperationalizingSoftgoalType):
    """Exception Handling technique type"""
    description = "Managing and responding to runtime errors and exceptions"
    
class SearchType(OperationalizingSoftgoalType):
    """Search technique type"""
    description = "Database or information search operations"


class DisplayType(OperationalizingSoftgoalType):
    """Display technique type"""
    description = "Data visualization and presentation operations"


class RefreshType(OperationalizingSoftgoalType):
    """Refresh technique type"""
    description = "Periodic data update operations"


class LogType(OperationalizingSoftgoalType):
    """Logging technique type"""
    description = "Recording system events, activities, or data changes"

class AuthorizationType(OperationalizingSoftgoalType):
    """Authentication technique type"""
    description = "Verifying user identity and authorizing access"

class AuthenticationType(OperationalizingSoftgoalType):
    """Authentication technique type"""
    description = "Verifying user identity and authorizing access"

class AccessRuleValidationType(OperationalizingSoftgoalType):
    """Authentication technique type"""
    description = " A set of rules or conditions applied to data fields (in tables, forms, queries) that verify data entered by users meets specific standards before it's stored."

class IdentificationType(OperationalizingSoftgoalType):
    """Identification operationalization type"""
    description = "The process of claiming an identity by presenting an identifier (username, user ID, email address, device ID, certificate). Distinct from authentication, which verifies the claimed identity."


class SyncType(OperationalizingSoftgoalType):
    """Synchronization technique type"""
    description = "Synchronizing or updating data across systems"


class MonitorType(OperationalizingSoftgoalType):
    """Monitoring technique type"""
    description = "Tracking, monitoring, or observing system behavior"


class ValidationType(OperationalizingSoftgoalType):
    """Validation technique type"""
    description = "Checking, verifying, or validating data or conditions"


class NotifyType(OperationalizingSoftgoalType):
    """Notification technique type"""
    description = "Sending alerts, notifications, or informing users"


class StoreType(OperationalizingSoftgoalType):
    """Storage technique type"""
    description = "Persisting, saving, or storing data"


class ExportType(OperationalizingSoftgoalType):
    """Export/Import technique type"""
    description = "Exporting or importing data to/from external systems"


class BackupType(OperationalizingSoftgoalType):
    """Backup/Restore technique type"""
    description = "Backing up or restoring data for recovery"


class CompressionType(OperationalizingSoftgoalType):
    """Compression technique type"""
    description = "Data size reduction through encoding algorithms"

class LoadBalancingType(OperationalizingSoftgoalType):
    """Load Balancing technique type"""
    description = "Distribution of workload across multiple computing resources"

class VirtualizationType(OperationalizingSoftgoalType):
    """Virtualization technique type"""
    description = "Abstraction of hardware resources into virtual instances"

class NetworkMonitoringType(OperationalizingSoftgoalType):
    """Network Monitoring technique type"""
    description = "Analysis and inspection of network traffic for security and performance"

class DataWarehouseType(OperationalizingSoftgoalType):
    """Data Warehouse technique type"""
    description = "Centralized storage and analytics for business intelligence"

class SimulationType(OperationalizingSoftgoalType):
    """Simulation technique type"""
    description = "Model-based computation for prediction and analysis"

class EarlyWarningType(OperationalizingSoftgoalType):
    """Early Warning technique type"""
    description = "Provide advance warnings before required actions to allow user preparation time"

class MultimodalFeedbackType(OperationalizingSoftgoalType):
    """Multimodal Feedback technique type"""
    description = "Provide information through multiple sensory channels (audio, haptic, visual)"

class PersonalizedInterfacesType(OperationalizingSoftgoalType):
    """Personalized Interfaces technique type"""
    description = "Customize interface based on individual user's experience and needs"

class ConciseAudioInstructionsType(OperationalizingSoftgoalType):
    """Concise Audio Instructions technique type"""
    description = "Provide minimal, short, and precise audio instructions to minimize cognitive load"

class NonSpeechAudioCuesType(OperationalizingSoftgoalType):
    """Non-Speech Audio Cues technique type"""
    description = "Use earcons and non-verbal sounds to convey information"

class SubMeterPositioningType(OperationalizingSoftgoalType):
    """Sub-Meter Positioning technique type"""
    description = "Maintain positioning accuracy at or below specific threshold for safe navigation"

class SensorFusionType(OperationalizingSoftgoalType):
    """Sensor Fusion technique type"""
    description = "Combine multiple sensor inputs (IMU, Wi-Fi, GPS, etc.) to improve accuracy"

class RapidTaskMasteryType(OperationalizingSoftgoalType):
    """Rapid Task Mastery technique type"""
    description = "Design interface to enable users to reach performance saturation within minimal repetitions"


# ----------------------------------------------------------------------------
# Softgoal Classes (for creating instances)
# ----------------------------------------------------------------------------

class PerformanceSoftgoal(NFRSoftgoal):
    """Performance softgoal class"""
    type = PerformanceType  # Class-level attribute


class TimePerformanceSoftgoal(NFRSoftgoal):
    """Time performance softgoal class"""
    type = TimePerformanceType


class SpacePerformanceSoftgoal(NFRSoftgoal):
    """Space performance softgoal class"""
    type = SpacePerformanceType


class ResponsivenessPerformanceSoftgoal(NFRSoftgoal):
    """Responsiveness performance softgoal class"""
    type = ResponsivenessPerformanceType


# Windows Task Manager Performance Softgoal Classes
class CPUUtilizationSoftgoal(NFRSoftgoal):
    """CPU utilization softgoal class"""
    type = CPUUtilizationType


class MemoryUsageSoftgoal(NFRSoftgoal):
    """Memory usage softgoal class"""
    type = MemoryUsageType


class DiskTimeSoftgoal(NFRSoftgoal):
    """Disk time softgoal class"""
    type = DiskTimeType


class NetworkThroughputSoftgoal(NFRSoftgoal):
    """Network throughput softgoal class"""
    type = NetworkThroughputType


class GPUUtilizationSoftgoal(NFRSoftgoal):
    """GPU utilization softgoal class"""
    type = GPUUtilizationType


class SecuritySoftgoal(NFRSoftgoal):
    """Security softgoal class"""
    type = SecurityType


class ConfidentialitySoftgoal(NFRSoftgoal):
    """Confidentiality softgoal class"""
    type = ConfidentialityType


class IntegritySoftgoal(NFRSoftgoal):
    """Integrity softgoal class"""
    type = IntegrityType


class AvailabilitySoftgoal(NFRSoftgoal):
    """Availability softgoal class"""
    type = AvailabilityType


class UsabilitySoftgoal(NFRSoftgoal):
    """Usability softgoal class"""
    type = UsabilityType


class ReliabilitySoftgoal(NFRSoftgoal):
    """Reliability softgoal class"""
    type = ReliabilityType


class MaintainabilitySoftgoal(NFRSoftgoal):
    """Maintainability softgoal class"""
    type = MaintainabilityType


# Additional NFR Softgoal Classes (alphabetically ordered)
class AccuracySoftgoal(NFRSoftgoal):
    """Accuracy softgoal class"""
    type = AccuracyType


class AdaptabilitySoftgoal(NFRSoftgoal):
    """Adaptability softgoal class"""
    type = AdaptabilityType


class BiasSoftgoal(NFRSoftgoal):
    """Bias softgoal class"""
    type = BiasType


class CompletenessSoftgoal(NFRSoftgoal):
    """Completeness softgoal class"""
    type = CompletenessType


class ComplexitySoftgoal(NFRSoftgoal):
    """Complexity softgoal class"""
    type = ComplexityType


class ConsistencySoftgoal(NFRSoftgoal):
    """Consistency softgoal class"""
    type = ConsistencyType


class CorrectnessSoftgoal(NFRSoftgoal):
    """Correctness softgoal class"""
    type = CorrectnessType


class DomainAdaptationSoftgoal(NFRSoftgoal):
    """Domain Adaptation softgoal class"""
    type = DomainAdaptationType


class EfficiencySoftgoal(NFRSoftgoal):
    """Efficiency softgoal class"""
    type = EfficiencyType


class EthicsSoftgoal(NFRSoftgoal):
    """Ethics softgoal class"""
    type = EthicsType


class ExplainabilitySoftgoal(NFRSoftgoal):
    """Explainability softgoal class"""
    type = ExplainabilityType


class FairnessSoftgoal(NFRSoftgoal):
    """Fairness softgoal class"""
    type = FairnessType


class FaultToleranceSoftgoal(NFRSoftgoal):
    """Fault Tolerance softgoal class"""
    type = FaultToleranceType


class FlexibilitySoftgoal(NFRSoftgoal):
    """Flexibility softgoal class"""
    type = FlexibilityType


class InterpretabilitySoftgoal(NFRSoftgoal):
    """Interpretability softgoal class"""
    type = InterpretabilityType


class InteroperabilitySoftgoal(NFRSoftgoal):
    """Interoperability softgoal class"""
    type = InteroperabilityType


class JustifiabilitySoftgoal(NFRSoftgoal):
    """Justifiability softgoal class"""
    type = JustifiabilityType


class PortabilitySoftgoal(NFRSoftgoal):
    """Portability softgoal class"""
    type = PortabilityType


class PrivacySoftgoal(NFRSoftgoal):
    """Privacy softgoal class"""
    type = PrivacyType


class RepeatabilitySoftgoal(NFRSoftgoal):
    """Repeatability softgoal class"""
    type = RepeatabilityType


class RetrainabilitySoftgoal(NFRSoftgoal):
    """Retrainability softgoal class"""
    type = RetrainabilityType


class ReproducibilitySoftgoal(NFRSoftgoal):
    """Reproducibility softgoal class"""
    type = ReproducibilityType


class ReusabilitySoftgoal(NFRSoftgoal):
    """Reusability softgoal class"""
    type = ReusabilityType


class SafetySoftgoal(NFRSoftgoal):
    """Safety softgoal class"""
    type = SafetyType


class ScalabilitySoftgoal(NFRSoftgoal):
    """Scalability softgoal class"""
    type = ScalabilityType


class TestabilitySoftgoal(NFRSoftgoal):
    """Testability softgoal class"""
    type = TestabilityType


class TransparencySoftgoal(NFRSoftgoal):
    """Transparency softgoal class"""
    type = TransparencyType


class TraceabilitySoftgoal(NFRSoftgoal):
    """Traceability softgoal class"""
    type = TraceabilityType


class TrustSoftgoal(NFRSoftgoal):
    """Trust softgoal class"""
    type = TrustType


class LegalComplianceSoftgoal(NFRSoftgoal):
    """Legal Compliance softgoal class"""
    type = LegalComplianceType


class LookFeelSoftgoal(NFRSoftgoal):
    """Look and Feel softgoal class"""
    type = LookFeelType

class RecoverabilitySoftgoal(NFRSoftgoal):
    """Recoverability softgoal class"""
    type = RecoverabilityType

class DiagnosabilitySoftgoal(NFRSoftgoal):
    """Diagnosability softgoal class"""
    type = DiagnosabilityType

class CompatibilitySoftgoal(NFRSoftgoal):
    """Compatibility softgoal class"""
    type = CompatibilityType

class DeterministicBehaviorSoftgoal(NFRSoftgoal):
    """Deterministic Behavior softgoal class"""
    type = DeterministicBehaviorType    

class LearnabilitySoftgoal(NFRSoftgoal):
    """Learnability softgoal class"""
    type = LearnabilityType

class MemorabilitySoftgoal(NFRSoftgoal):
    """Memorability softgoal class"""
    type = MemorabilityType

class ErrorPreventionSoftgoal(NFRSoftgoal):
    """Error Prevention softgoal class"""
    type = ErrorPreventionType

class SatisfactionSoftgoal(NFRSoftgoal):
    """Satisfaction softgoal class"""
    type = SatisfactionType


# Operationalizing Technique Softgoal Classes   

class IndexingSoftgoal(OperationalizingSoftgoal):
    """Indexing softgoal class"""
    type = IndexingType


class CachingSoftgoal(OperationalizingSoftgoal):
    """Caching softgoal class"""
    type = CachingType


class EncryptionSoftgoal(OperationalizingSoftgoal):
    """Encryption softgoal class"""
    type = EncryptionType

class SymmetricKeyEncryptionSoftgoal(EncryptionSoftgoal):
    """Symmetric-key encryption softgoal class"""
    type = SymmetricKeyEncryptionType

class PublicKeyEncryptionSoftgoal(EncryptionSoftgoal):
    """Public-key encryption softgoal class"""
    type = PublicKeyEncryptionType

class RSAEncryptionSoftgoal(PublicKeyEncryptionSoftgoal):
    """RSA encryption softgoal class"""
    type = RSAEncryptionType



class AuditingSoftgoal(OperationalizingSoftgoal):
    """Auditing softgoal class"""
    type = AuditingType

class ExceptionHandlingSoftgoal(OperationalizingSoftgoal):
    """Exception Handling softgoal class"""
    type = ExceptionHandlingType

class SearchSoftgoal(OperationalizingSoftgoal):
    """Search softgoal class"""
    type = SearchType

class DisplaySoftgoal(OperationalizingSoftgoal):
    """Display softgoal class"""
    type = DisplayType


class RefreshSoftgoal(OperationalizingSoftgoal):
    """Refresh softgoal class"""
    type = RefreshType


class LogSoftgoal(OperationalizingSoftgoal):
    """Logging softgoal class"""
    type = LogType


class AuthenticationSoftgoal(OperationalizingSoftgoal):
    """Authentication softgoal class"""
    type = AuthenticationType

class AuthorizationSoftgoal(OperationalizingSoftgoal):
    """Authentication softgoal class"""
    type = AuthorizationType

class AccessRuleValidationSoftgoal(OperationalizingSoftgoal):
    """Authentication softgoal class"""
    type = AccessRuleValidationType

class IdentificationSoftgoal(OperationalizingSoftgoal):
    """Authentication softgoal class"""
    type = IdentificationType

class SyncSoftgoal(OperationalizingSoftgoal):
    """Synchronization softgoal class"""
    type = SyncType


class MonitorSoftgoal(OperationalizingSoftgoal):
    """Monitoring softgoal class"""
    type = MonitorType


class ValidationSoftgoal(OperationalizingSoftgoal):
    """Validation softgoal class"""
    type = ValidationType


class NotifySoftgoal(OperationalizingSoftgoal):
    """Notification softgoal class"""
    type = NotifyType


class StoreSoftgoal(OperationalizingSoftgoal):
    """Storage softgoal class"""
    type = StoreType


class ExportSoftgoal(OperationalizingSoftgoal):
    """Export/Import softgoal class"""
    type = ExportType


class BackupSoftgoal(OperationalizingSoftgoal):
    """Backup/Restore softgoal class"""
    type = BackupType

class CompressionSoftgoal(OperationalizingSoftgoal):
    """Compression softgoal class"""
    type = CompressionType

class LoadBalancingSoftgoal(OperationalizingSoftgoal):
    """Load Balancing softgoal class"""
    type = LoadBalancingType

class VirtualizationSoftgoal(OperationalizingSoftgoal):
    """Virtualization softgoal class"""
    type = VirtualizationType

class NetworkMonitoringSoftgoal(OperationalizingSoftgoal):
    """Network Monitoring softgoal class"""
    type = NetworkMonitoringType

class DataWarehouseSoftgoal(OperationalizingSoftgoal):
    """Data Warehouse softgoal class"""
    type = DataWarehouseType

class SimulationSoftgoal(OperationalizingSoftgoal): 
    """Simulation softgoal class"""
    type = SimulationType

class EarlyWarningSoftgoal(OperationalizingSoftgoal):
    """Early Warning softgoal class"""
    type = EarlyWarningType

class MultimodalFeedbackSoftgoal(OperationalizingSoftgoal):
    """Multimodal Feedback softgoal class"""
    type = MultimodalFeedbackType

class PersonalizedInterfacesSoftgoal(OperationalizingSoftgoal):
    """Personalized Interfaces softgoal class"""
    type = PersonalizedInterfacesType

class ConciseAudioInstructionsSoftgoal(OperationalizingSoftgoal):
    """Concise Audio Instructions softgoal class"""
    type = ConciseAudioInstructionsType

class NonSpeechAudioCuesSoftgoal(OperationalizingSoftgoal):
    """Non-Speech Audio Cues softgoal class"""
    type = NonSpeechAudioCuesType

class SubMeterPositioningSoftgoal(OperationalizingSoftgoal):
    """Sub-Meter Positioning softgoal class"""
    type = SubMeterPositioningType

class SensorFusionSoftgoal(OperationalizingSoftgoal):
    """Sensor Fusion softgoal class"""
    type = SensorFusionType

class RapidTaskMasterySoftgoal(OperationalizingSoftgoal):
    """Rapid Task Mastery softgoal class"""
    type = RapidTaskMasteryType

# ----------------------------------------------------------------------------
# Method Classes
# ----------------------------------------------------------------------------

class Method(metaclass=MethodMetaClass):
    """Base class for all methods"""
    pass


class DecompositionMethod(Method, metaclass=DecompositionMethodMetaClass):
    """
    Decomposition method class.
    
    NO source attribute! Attribution via ClaimSoftgoals.
    """
    def __init__(self, name: str, parent, offspring: List):
        self.name = name
        self.parent = parent  # Parent type being decomposed
        self.offspring = offspring  # List of child types
        self.description = ""
    
    def __repr__(self):
        parent_name = self.parent.__name__ if hasattr(self.parent, '__name__') else str(self.parent)
        offspring_names = [o.__name__ if hasattr(o, '__name__') else str(o) for o in self.offspring]
        return f"DecompositionMethod('{self.name}', {parent_name} → {offspring_names})"

class NFRDecompositionMethod(DecompositionMethod, metaclass=NFRDecompositionMethodMetaClass):
    """Decomposition method for NFR softgoals"""
    pass

class PerformanceDecompositionMethod(NFRDecompositionMethod):
    """All Performance decompositions are instances of this"""
    parent = PerformanceType

class SecurityDecompositionMethod(NFRDecompositionMethod):
    """All Security decompositions are instances of this"""
    parent = SecurityType

class UsabilityDecompositionMethod(NFRDecompositionMethod):
    """All Usability decompositions are instances of this"""
    parent = UsabilityType


class OperationalizationDecompositionMethod(DecompositionMethod, metaclass=OperationalizationDecompositionMethodMetaClass):
    """Decomposition method for Operationalization softgoals"""
    pass

class AuthorizationDecompositionMethod(OperationalizationDecompositionMethod):
    """All Authorization decompositions are instances of this"""
    parent = AuthorizationType

class ClaimDecompositionMethod(DecompositionMethod, metaclass=ClaimDecompositionMethodMetaClass):
    """Decomposition method for Claim softgoals"""
    pass


class Contribution(Proposition, metaclass=ContributionMetaClass):
    """Contribution relationship between softgoals"""
    def __init__(self, source_name: str, target_name: str, contribution_type: ContributionType):
        super().__init__()
        self.source = source_name
        self.target = target_name
        self.type = contribution_type


# ============================================================================
# LEVEL 3: GROUND INSTANCES
# ============================================================================

print("  ✓ Level 1 (Metamodel): Metaclasses defined")
print("  ✓ Level 2 (Model): Classes defined")

# ----------------------------------------------------------------------------
# Decomposition Method Instances (NO source attribute!)
# ----------------------------------------------------------------------------

# Performance decomposition - Traditional CS approach
PerformanceDecomp1 = PerformanceDecompositionMethod(
    name="Performance Type Decomposition 1",
    parent=PerformanceType,
    offspring=[TimePerformanceType, SpacePerformanceType]
)
PerformanceDecomp1.description = "Two-way decomposition of Performance into Time and Space"

# Performance decomposition - Smith's approach
PerformanceDecomp2 = PerformanceDecompositionMethod(
    name="Performance Type Decomposition 2",
    parent=PerformanceType,
    offspring=[TimePerformanceType, SpacePerformanceType, ResponsivenessPerformanceType]
)
PerformanceDecomp2.description = "Three-way decomposition including user-perceived responsiveness"

# Security decomposition - CIA Triad
SecurityDecomp1 = SecurityDecompositionMethod(
    name="Security Type Decomposition 1",
    parent=SecurityType,
    offspring=[ConfidentialityType, IntegrityType, AvailabilityType]
)
SecurityDecomp1.description = "Classic CIA triad decomposition"

# Performance decomposition - Windows Task Manager approach
PerformanceDecomp3 = PerformanceDecompositionMethod(
    name="Performance Type Decomposition 3",
    parent=PerformanceType,
    offspring=[CPUUtilizationType, MemoryUsageType, DiskTimeType, NetworkThroughputType, GPUUtilizationType]
)
PerformanceDecomp3.description = "Five-way decomposition based on Windows Task Manager Performance tab: CPU, Memory, Disk, Network, GPU"

AuthorizationDecomp1 = AuthorizationDecompositionMethod(
    name="Authorization Type Decomposition 1",
    parent=AuthorizationType,
    offspring=[IdentificationType, AuthenticationType, AccessRuleValidationType]
)

UsabilityDecomp_ISO25010 = UsabilityDecompositionMethod(
    name="ISO 25010 Usability Decomposition",
    parent=UsabilityType,
    offspring=[LearnabilityType, EfficiencyType, MemorabilityType, ErrorPreventionType, SatisfactionType]
)
UsabilityDecomp_ISO25010.description = "ISO/IEC 25010 standard decomposition of Usability into five quality sub-characteristics"



# ----------------------------------------------------------------------------
# ClaimSoftgoal Instances (Attribution & Argumentation)
# ----------------------------------------------------------------------------

# Claim about PerformanceDecomp1 (Traditional CS)
claim_performance_traditionalCS = ClaimSoftgoal()
claim_performance_traditionalCS.type = TraditionalCSPerformanceClaimType
claim_performance_traditionalCS.topic = SoftgoalTopic("Performance Decomposition")

# Claim about PerformanceDecomp2 (Smith's approach)
claim_performance_smith = ClaimSoftgoal()
claim_performance_smith.type = SmithPerformanceClaimType
claim_performance_smith.topic = SoftgoalTopic("Performance Decomposition")

# Claim about SecurityDecomp1 (CIA Triad)
claim_security_cia = ClaimSoftgoal()
claim_security_cia.type = CIATriadClaimType
claim_security_cia.topic = SoftgoalTopic("Security Decomposition")

# Claim about PerformanceDecomp3 (Windows Task Manager)
claim_performance_windows = ClaimSoftgoal()
claim_performance_windows.type = WindowsTaskManagerClaimType
claim_performance_windows.topic = SoftgoalTopic("Performance Decomposition")

# Claim about Encryption Types
claim_encryption_types = ClaimSoftgoal()
claim_encryption_types.type = WikipediaEncryptionTypesClaimType
claim_encryption_types.topic = SoftgoalTopic("Encryption Sub-classes")

# Claim about UsabilityDecomp_ISO25010
claim_usability_iso25010 = ClaimSoftgoal()
claim_usability_iso25010.type = ISO25010UsabilityClaimType
claim_usability_iso25010.topic = SoftgoalTopic("Usability Decomposition")

claim_earlywarning_safety = ClaimSoftgoal()
claim_earlywarning_safety.type = ManduchiSafetyClaimType
claim_earlywarning_safety.topic = SoftgoalTopic("EarlyWarning")

claim_multimodal_usability = ClaimSoftgoal()
claim_multimodal_usability.type = ManduchiUsabilityClaimType
claim_multimodal_usability.topic = SoftgoalTopic("MultimodalFeedback")

# Claim about Personalized Interfaces operationalizing Usability
claim_personalized_usability = ClaimSoftgoal()
claim_personalized_usability.type = ASSISTUsabilityClaimType
claim_personalized_usability.topic = SoftgoalTopic("PersonalizedInterfaces")

# Claim about Concise Audio operationalizing Usability
claim_conciseaudio_usability = ClaimSoftgoal()
claim_conciseaudio_usability.type = PMCCognitiveLoadClaimType
claim_conciseaudio_usability.topic = SoftgoalTopic("ConciseAudioInstructions")

# Claim about Non-Speech Sounds operationalizing Usability
claim_nonspeech_usability = ClaimSoftgoal()
claim_nonspeech_usability.type = PMCReceptivityClaimType
claim_nonspeech_usability.topic = SoftgoalTopic("NonSpeechAudioCues")

# Claim about Sub-Meter Positioning operationalizing Safety
claim_positioning_safety = ClaimSoftgoal()
claim_positioning_safety.type = SensorsSafetyClaimType
claim_positioning_safety.topic = SoftgoalTopic("PositioningAccuracy")

# Claim about Sensor Fusion operationalizing Accuracy
claim_sensorfusion_accuracy = ClaimSoftgoal()
claim_sensorfusion_accuracy.type = PouloseSensorFusionClaimType
claim_sensorfusion_accuracy.topic = SoftgoalTopic("SensorFusion")

# Claim about Rapid Task Mastery operationalizing Learnability
claim_rapidmastery_learnability = ClaimSoftgoal()
claim_rapidmastery_learnability.type = NielsenLearnabilityClaimType
claim_rapidmastery_learnability.topic = SoftgoalTopic("RapidTaskMastery")


# ----------------------------------------------------------------------------
# NFR Softgoal Instances (Examples)
# ----------------------------------------------------------------------------

# Example 1: Specific performance NFR using traditional decomposition
performanceNFR1 = TimePerformanceSoftgoal()
performanceNFR1.topic = SoftgoalTopic("API Response Time")
performanceNFR1.priority = PropositionPriority.CRITICAL
performanceNFR1.description = "API must respond within 200ms for 95th percentile"
performanceNFR1.label = PropositionLabel.SATISFICED

# Example 2: Specific security NFR using CIA triad
confidentialityNFR1 = ConfidentialitySoftgoal()
confidentialityNFR1.topic = SoftgoalTopic("User Password Storage")
confidentialityNFR1.priority = PropositionPriority.CRITICAL
confidentialityNFR1.description = "User passwords must be hashed using bcrypt with work factor 12"
confidentialityNFR1.label = PropositionLabel.SATISFICED

# Example 3: 
pgp_implementation = PublicKeyEncryptionType()
pgp_implementation.type = PublicKeyEncryptionType  # Or a more specific type
pgp_implementation.topic = SoftgoalTopic("Pretty Good Privacy (PGP)")
pgp_implementation.is_ground_instance = True  # If you have this flag


EarlyWarningToSafety = Contribution("EarlyWarning", "Safety", ContributionType.HELP)






# ----------------------------------------------------------------------------
# Contribution Instances (Examples)
# ----------------------------------------------------------------------------

# ops for perf => timeperf + perf + others


# ops for timeperf
IndexingToTimePerformance = Contribution("Indexing", "TimePerformance", ContributionType.HELP)
CachingToTimePerformance = Contribution("Caching", "TimePerformance", ContributionType.HELP)
EncryptionToTimePerformance = Contribution("Encryption", "TimePerformance", ContributionType.HURT)
CompressionToPerformance = Contribution("Compression", "TimePerformance", ContributionType.HELP)
NetworkMonitoringToTimePerformance = Contribution("NetworkMonitoring", "TimePerformance", ContributionType.HURT) # Packet inspection overhead

#ops for spacePerf
IndexingToSpacePerformance = Contribution("Indexing", "SpacePerformance", ContributionType.HELP)
CachingToSpacePerformance = Contribution("Caching", "SpacePerformance", ContributionType.HELP)
CompressionToSpacePerformance = Contribution("Compression", "SpacePerformance", ContributionType.HELP)

#ops for confidentiality
AuthenticationToConfidentiality = Contribution("Authentication", "Confidentiality", ContributionType.HELP)
EncryptionToConfidentiality = Contribution("Encryption", "Confidentiality", ContributionType.HELP)
NetworkMonitoringToConfidentiality = Contribution("NetworkMonitoring", "Confidentiality", ContributionType.HELP)
AccessRuleValidationToConfidentiality = Contribution("AccessRuleValidation", "Confidentiality", ContributionType.HELP)
AuthorizationToConfidentiality = Contribution("Authorization", "Confidentiality", ContributionType.HELP)

#ops for security
AuthenticationToSecurity = Contribution("Authentication", "Security", ContributionType.HELP)
EncryptionToSecurity = Contribution("Encryption", "Security", ContributionType.HELP)
NetworkMonitoringToSecurity = Contribution("NetworkMonitoring", "Security", ContributionType.HELP)

#ops for integrity
AuthenticationToIntegrity = Contribution("Authentication", "Integrity", ContributionType.HELP)

#ops for accuracy
AuditingToAccuracy = Contribution("Auditing", "Accuracy", ContributionType.HELP)
AuditingToSecurity = Contribution("Auditing", "Security", ContributionType.HELP)
ValidationToAccuracy = Contribution("Validation", "Accuracy", ContributionType.HELP)
ExceptionHandlingToAccuracy = Contribution("ExceptionHandling", "Accuracy", ContributionType.HELP)
SensorFusionToAccuracy = Contribution("SensorFusion", "Accuracy", ContributionType.HELP)

#ops for scalability
LoadBalancingToScalability = Contribution("LoadBalancing", "Scalability", ContributionType.HELP)

#ops for consistency
CachingToConsistency = Contribution("Caching", "Consistency", ContributionType.HURT)


#ops for portability
VirtualizationToPortability = Contribution("Virtualization", "Portability", ContributionType.HELP)

#ops for diagnosability and recoverability
LoggingToDiagnosability = Contribution("Logging", "Diagnosability", ContributionType.HELP)
BackupToRecoverability = Contribution("Backup", "Recoverability", ContributionType.MAKE)

#ops for usability
MultimodalFeedbackToUsability = Contribution("MultimodalFeedback", "Usability", ContributionType.HELP)
PersonalizedInterfacesToUsability = Contribution("PersonalizedInterfaces", "Usability", ContributionType.HELP)
ConciseAudioInstructionsToUsability = Contribution("ConciseAudioInstructions", "Usability", ContributionType.HELP)
NonSpeechAudioCuesToUsability = Contribution("NonSpeechAudioCues", "Usability", ContributionType.HELP)

#ops for safety
SubMeterPositioningToSafety = Contribution("SubMeterPositioning", "Safety", ContributionType.HELP)

#learnability
RapidTaskMasteryToLearnability = Contribution("RapidTaskMastery", "Learnability", ContributionType.MAKE)

print("  ✓ Level 3 (Ground Instances): Instances created")
print()

# ============================================================================
# SUMMARY
# ============================================================================

print("="*70)
print("NFR FRAMEWORK V2 - CLAIMSOFTGOAL APPROACH")
print("="*70)
print()
print("LEVEL 1 (Metaclasses):")
print("  • PropositionMetaClass")
print("  • SoftgoalMetaClass → [NFRSoftgoalMetaClass, OperationalizingSoftgoalMetaClass, ClaimSoftgoalMetaClass]")
print("  • SoftgoalTypeMetaClass")
print("  • DecompositionMethodMetaClass")
print()
print("LEVEL 2 (Classes/Types):")
print("  • SoftgoalType:")
print("    - NFRSoftgoalType: PerformanceType, SecurityType, etc.")
print("    - OperationalizingSoftgoalType: IndexingType, CachingType, etc.")
print("  • Softgoal:")
print("    - NFRSoftgoal: PerformanceSoftgoal, SecuritySoftgoal, etc.")
print("    - OperationalizingSoftgoal: IndexingSoftgoal, CachingSoftgoal, etc.")
print("    - ClaimSoftgoal (for argumentation)")
print("  • DecompositionMethod (NO source attribute)")
print()
print("LEVEL 3 (Ground Instances):")
print("  • 4 DecompositionMethod instances (Traditional CS, Smith, CIA Triad, Windows Task Manager)")
print("  • 4 ClaimSoftgoal instances (with attribution & justification)")
print()
print("KEY DESIGN DECISION:")
print("  ✓ DecompositionMethod has NO source attribute, ALL attribution via ClaimSoftgoals")
print()
print("="*70)
print("✅ 3-Level Metamodel V2 Successfully Built!")
print("="*70)